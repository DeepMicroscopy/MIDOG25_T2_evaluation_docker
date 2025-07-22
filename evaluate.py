"""
The following is a simple example evaluation method.

It is meant to run within a container. Its steps are as follows:

  1. Read the algorithm output
  2. Associate original algorithm inputs with a ground truths via predictions.json
  3. Calculate metrics by comparing the algorithm output to the ground truth
  4. Repeat for all algorithm jobs that ran for this submission
  5. Aggregate the calculated metrics
  6. Save the metrics to metrics.json

To run it locally, you can call the following bash script:

  ./do_test_run.sh

This will start the evaluation and reads from ./test/input and writes to ./test/output

To save the container and prep it for upload to Grand-Challenge.org you can call:

  ./do_save.sh

Any container that shows the same behaviour will do, this is purely an example of how one COULD do it.

Reference the documentation to get details on the runtime environment on the platform:
https://grand-challenge.org/documentation/runtime-environment/

Happy programming!
"""

import json
from sklearn.metrics import roc_auc_score, accuracy_score, recall_score, precision_score

import random
import numpy as np 
from pathlib import Path
from pprint import pformat, pprint
from helpers import run_prediction_processing, tree

INPUT_DIRECTORY = Path("/input")
OUTPUT_DIRECTORY = Path("/output")


def main():
    print_inputs()

    metrics = {}
    predictions = read_predictions()

    # We now process each algorithm job for this submission
    # Note that the jobs are not in any specific order!
    # We work that out from predictions.json

    # Use concurrent workers to process the predictions more efficiently
    metrics["results"] = run_prediction_processing(fn=process, predictions=predictions)

    # We have the results per prediction, we can aggregate the results and
    # generate an overall score(s) for this submission

    total_tps = int(np.sum([r["tps"] for r in metrics['results']]))
    total_fps = int(np.sum([r["fps"] for r in metrics['results']]))
    total_fns = int(np.sum([r["fns"] for r in metrics['results']]))
    total_tns = int(np.sum([r["tns"] for r in metrics['results']]))
    total_sens = total_tps / (total_tps + total_fns)
    total_spec = total_tns / (total_tns + total_fps)
    all_gt = np.hstack([r['gt'] for r in metrics['results']])
    all_pred = np.hstack([r['output'] for r in metrics['results']])
    all_score = np.hstack([r['score'] for r in metrics['results']])
    roc_auc = roc_auc_score(all_gt, all_score)

    tumordomain = np.hstack([r['tumor_domains'] for r in metrics['results']])
    unique_tds = np.sort(np.unique(tumordomain))

    if metrics["results"]:
        metrics["aggregates"] = {
            "overall_sensitivity": float(total_sens),
            "overall_specificity": float(total_spec),
            "overall_balanced_accuracy" : float((total_spec+total_sens)/2),
            "overall_roc_auc" : roc_auc,
            "overall_accuracy" : float((total_tps+total_tns)/(total_tps+total_fns+total_fps+total_tns))
        }

        for td in unique_tds:
            sens=recall_score(y_true=all_gt[tumordomain == td], y_pred=all_pred[tumordomain==td])
            spec=recall_score(y_true=all_gt[tumordomain == td], y_pred=all_pred[tumordomain==td],pos_label=0)
            metrics["aggregates"][f"domain_{td}"] = {
                "sensitivity": sens,
                "specificity": spec,
                "balanced_accuracy": (sens+spec)/2, 
                "accuracy" : accuracy_score(y_true=all_gt[tumordomain == td], y_pred=all_pred[tumordomain==td]),
                "roc_auc" : roc_auc_score(y_true=all_gt[tumordomain == td], y_score=all_score[tumordomain == td])
            }

    metrics['results'] = {} # clear results to not show individual results in log

    # Make sure to save the metrics
    write_metrics(metrics=metrics)

    return 0


def process(job):
    # The key is a tuple of the slugs of the input sockets
    interface_key = get_interface_key(job)

    # Lookup the handler for this particular set of sockets (i.e. the interface)
    handler = {
        ("stacked-histopathology-roi-cropouts",): process_interf0,
    }[interface_key]

    # Call the handler
    return handler(job)


def process_interf0(
    job,
):
    """Processes a single algorithm job, looking at the outputs"""
    report = "Processing:\n"
    report += pformat(job)
    report += "\n"

    # Firstly, find the location of the results
    location_multiple_mitotic_figure_classification = get_file_location(
        job_pk=job["pk"],
        values=job["outputs"],
        slug="multiple-mitotic-figure-classification",
    )

    # Secondly, read the results
    result_multiple_mitotic_figure_classification = load_json_file(
        location=location_multiple_mitotic_figure_classification,
    )

    # Thirdly, retrieve the input file name to match it with your ground truth
    image_name_stacked_histopathology_roi_cropouts = get_image_name(
        values=job["inputs"],
        slug="stacked-histopathology-roi-cropouts",
    )

    # Fourthly, load your ground truth
    # Include your ground truth in one of two ways:

    # Option 2: upload it as a tarball to Grand Challenge
    # Go to phase settings and upload it under Ground Truths. Your ground truth will be extracted to `ground_truth_dir` at runtime.
    ground_truth_dir = Path("/opt/ml/input/data/ground_truth")
    with open(
        ground_truth_dir / "ground_truth.json", "r"
    ) as f:
        truth = f.read()


    report += truth
    #print(report)
    classes_to_ids={'normal':0, 'atypical':1}


    truth = json.loads(truth)
    truth_dict = {x['image'] : x['labels'] for x in truth}
    domain_dict = {x['image'] : x['tumordomains'] for x in truth}

    if image_name_stacked_histopathology_roi_cropouts not in truth_dict:
        raise ValueError('No GT for this image: '+str(image_name_stacked_histopathology_roi_cropouts))

    if len(result_multiple_mitotic_figure_classification) != len(truth_dict[image_name_stacked_histopathology_roi_cropouts]):
        raise ValueError(f'Results length does not match GT length. (result lengths={len(result_multiple_mitotic_figure_classification)}, GT length={len(truth_dict[image_name_stacked_histopathology_roi_cropouts])})')
    
    output=[]
    output_prob = []
    prob_atypical = []
    tumordomains = []

    for res in result_multiple_mitotic_figure_classification:
        if not isinstance(res,dict):
            raise TypeError('Output format is wrong. Needs list of dictionaries.')
        if ('class' not in res) or ('confidence' not in res):
            raise NameError('Output format is wrong. Needs to be list of dictionaries with entries "class" and "confidence"')
        if (res['class'] not in classes_to_ids.keys()):
            raise NameError('Output format is wrong. Class needs to be either normal or atypical.')
        if not isinstance(res['confidence'], float):
            raise NameError('Output format is wrong. Confidence needs to be of type float.')


        output.append(classes_to_ids[res['class']])
        output_prob.append(res['confidence'])

        # calculate the prob for atypical 
        prob_atypical.append(res['confidence'] if res['class']=='atypical' else 1-res['confidence'])

    y_true = np.array([classes_to_ids[x] for x in truth_dict[image_name_stacked_histopathology_roi_cropouts]])
    output = np.array(output)
    
    tps = int(np.sum((output==1) & (y_true == 1)))
    fps = int(np.sum((output==1) & (y_true == 0)))
    fns = int(np.sum((output==0) & (y_true == 1)))
    tns = int(np.sum((output==0) & (y_true == 0)))
    
    # Report back metrics but also the raw results (for ROC AUC)
    return {
        "tps" : tps,
        "fps" : fps,
        "fns" : fns,
        "tns" : tns,
        "output" : output.tolist(),
        "gt" : y_true.tolist(),
        "score" : prob_atypical,
        "tumor_domains" : domain_dict[image_name_stacked_histopathology_roi_cropouts],
    }


def print_inputs():
    # Just for convenience, in the logs you can then see what files you have to work with
    print("Input Files:")
    for line in tree(INPUT_DIRECTORY):
        print(line)
    print("")


def read_predictions():
    # The prediction file tells us the location of the users' predictions
    return load_json_file(location=INPUT_DIRECTORY / "predictions.json")


def get_interface_key(job):
    # Each interface has a unique key that is the set of socket slugs given as input
    socket_slugs = [sv["interface"]["slug"] for sv in job["inputs"]]
    return tuple(sorted(socket_slugs))


def get_image_name(*, values, slug):
    # This tells us the user-provided name of the input or output image
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["image"]["name"]

    raise RuntimeError(f"Image with interface {slug} not found!")


def get_interface_relative_path(*, values, slug):
    # Gets the location of the interface relative to the input or output
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["interface"]["relative_path"]

    raise RuntimeError(f"Value with interface {slug} not found!")


def get_file_location(*, job_pk, values, slug):
    # Where a job's output file will be located in the evaluation container
    relative_path = get_interface_relative_path(values=values, slug=slug)
    return INPUT_DIRECTORY / job_pk / "output" / relative_path


def load_json_file(*, location):
    # Reads a json file
    with open(location) as f:
        return json.loads(f.read())


def write_metrics(*, metrics):
    # Write a json document used for ranking results on the leaderboard
    write_json_file(location=OUTPUT_DIRECTORY / "metrics.json", content=metrics)


def write_json_file(*, location, content):
    # Writes a json file
    with open(location, "w") as f:
        f.write(json.dumps(content, indent=4))


if __name__ == "__main__":
    raise SystemExit(main())
