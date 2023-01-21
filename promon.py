import subprocess
import prometheus_client
import re
import statistics
import os
import json
import glob
import datetime

FPING_CMDLINE = "fping -p 100 -C 30 -B 1 -q -r 1".split(" ")
FPING_REGEX = re.compile(r"^(\S*)\s*: (.*)$", re.MULTILINE)
CONFIG_PATH = "./targets.json"
labeled_prom_metrics = {"cluster_targets": [], "external_targets": []}

registry = prometheus_client.CollectorRegistry()
prom_metrics_cluster = {"sent": prometheus_client.Counter('kube_node_ping_packets_sent_total',
                                                  'ICMP packets sent',
                                                  ['destination_node', 'destination_node_ip_address'],
                                                  registry=registry),
                "received": prometheus_client.Counter('kube_node_ping_packets_received_total',
                                                      'ICMP packets received',
                                                     ['destination_node', 'destination_node_ip_address'],
                                                     registry=registry),
                "rtt": prometheus_client.Counter('kube_node_ping_rtt_milliseconds_total',
                                                 'round-trip time',
                                                ['destination_node', 'destination_node_ip_address'],
                                                registry=registry),
                "min": prometheus_client.Gauge('kube_node_ping_rtt_min', 'minimum round-trip time',
                                               ['destination_node', 'destination_node_ip_address'],
                                               registry=registry),
                "max": prometheus_client.Gauge('kube_node_ping_rtt_max', 'maximum round-trip time',
                                               ['destination_node', 'destination_node_ip_address'],
                                               registry=registry),
                "mdev": prometheus_client.Gauge('kube_node_ping_rtt_mdev',
                                                'mean deviation of round-trip times',
                                                ['destination_node', 'destination_node_ip_address'],
                                                registry=registry)}




def compute_results(results):
    computed = {}

    matches = FPING_REGEX.finditer(results)
    for match in matches:
        host = match.group(1)
        ping_results = match.group(2)
        if "duplicate" in ping_results:
            continue
        splitted = ping_results.split(" ")
        if len(splitted) != 30:
            raise ValueError("ping returned wrong number of results: \"{}\"".format(splitted))

        positive_results = [float(x) for x in splitted if x != "-"]
        if len(positive_results) > 0:
            computed[host] = {"sent": 30, "received": len(positive_results),
                            "rtt": sum(positive_results),
                            "max": max(positive_results), "min": min(positive_results),
                            "mdev": statistics.pstdev(positive_results)}
        else:
            computed[host] = {"sent": 30, "received": len(positive_results), "rtt": 0,
                            "max": 0, "min": 0, "mdev": 0}
    if not len(computed):
        raise ValueError("regex match\"{}\" found nothing in fping output \"{}\"".format(FPING_REGEX, results))
    return computed


def call_fping(ips):
    print(type(FPING_CMDLINE))
    cmdline = FPING_CMDLINE + [ips]
    print("Aici",cmdline)
    process = subprocess.run(cmdline, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, universal_newlines=True)
    if process.returncode == 3:
        raise ValueError("invalid arguments: {}".format(cmdline))
    if process.returncode == 4:
        raise OSError("fping reported syscall error: {}".format(process.stderr))
    return process.stdout


if __name__ == "__main__":
  host = ["8.8.8.8", "1.1.1.1"]
  for value in host:
    out = call_fping(value)
    results = compute_results(out)
    print(results)
    #print(type(results))
    #c = Counter('my_failures', 'Description of counter')
    #c.set(12)
    #print(results)


  #print(type(FPING_CMDLINE))
"""
  while True:
    with open(CONFIG_PATH, "r") as f:
        config = json.loads(f.read())
        config["external_targets"] = [] if config["external_targets"] is None else config["external_targets"]
        #print(config["external_targets"])
        for target in config["external_targets"]:
            target["name"] = target["host"] if "name" not in target.keys() else target["name"]
    if labeled_prom_metrics["cluster_targets"]:
       for metric in labeled_prom_metrics["cluster_targets"]:
           print(labeled_prom_metrics["cluster_targets"])
           if (metric["node_name"], metric["ip"]) not in [(node["name"], node["ipAddress"]) for node in config['cluster_targets']]:
               print(node["name"])
               for k, v in prom_metrics_cluster.items():
                   v.remove(metric["node_name"], metric["ip"])

    if labeled_prom_metrics["external_targets"]:
       for metric in labeled_prom_metrics["external_targets"]:
           if (metric["target_name"], metric["host"]) not in [(target["name"], target["host"]) for target in config['external_targets']]:
               for k, v in prom_metrics_external.items():
                   v.remove(metric["target_name"], metric["host"])

    for node in config["cluster_targets"]:
       #print(node)
       metrics = {"node_name": node["name"], "ip": node["ipAddress"], "prom_metrics": {}}
       print(metrics)
       for k, v in prom_metrics_cluster.items():
          print("K Value",k)
          #print("V Value",v)
          #metrics["prom_metrics"][k] = v.labels(node["name"], node["ipAddress"])

"""
