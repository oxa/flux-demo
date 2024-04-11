#!/usr/bin/env python3

import requests
import dotenv
import os
import argparse
import time

dotenv.load_dotenv()
PANOPTICA_API_KEY = os.getenv('PANOPTICA_TOKEN')

kustomize="""
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: panoptica
resources:
  - ../base/panoptica
patches:
  - path: panoptica-patch.yaml
    target:
      kind: HelmRelease
"""

base_tmpl = """
---
apiVersion: helm.toolkit.fluxcd.io/v2beta2
kind: HelmRelease
metadata:
  name: panoptica
  namespace: panoptica
spec:
  chart:
    spec:
      version: 1.2.3
  values:
{data}
"""
def indent_text(text, spaces=4):
    indentation = ' ' * spaces
    return '\n'.join(indentation + line if line else line for line in text.split('\n'))

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Process some booleans and a cluster name.")

    # Add the cluster-name argument
    parser.add_argument('cluster_name', type=str, help='The name of the cluster')

    # Add boolean flags
    parser.add_argument('--kspm', action='store_true', help='Enable KSPM feature', default=True)
    parser.add_argument('--cdr', action='store_true', help='Enable CDR feature', default=False)
    parser.add_argument('--apisecurity', action='store_true', help='Enable API Security feature',default=False)

    # Parse the arguments
    args = parser.parse_args()
    
    url = "https://api.us1.console.panoptica.app/api/kis/integrations"

    new_cluster = True
    # Verify intergration doesnt alraedy exist

    headers = {
        "accept": "application/json",
        "Authorization": PANOPTICA_API_KEY
    }

    response = requests.get(url, headers=headers)

    for integration in response.json()['items']:
        if integration['metadata']['name'] == args.cluster_name:
            print(f"Integration with name {args.cluster_name} already exists")
            integration_id = integration['metadata']['id']
            new_cluster = False
            break


    payload = {
        "metadata": { "name": f"{args.cluster_name}" },
        "apiSecurity": { "enabled": args.apisecurity },
        "detectionAndResponse": { "enabled": args.cdr },
        "kubernetesWorkloadSecurity": { "enabled": args.kspm }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": PANOPTICA_API_KEY
    }
    if new_cluster:
        response = requests.post(url, json=payload, headers=headers)
        response_json = response.json()
        integration_id = response_json["metadata"]["id"]
        print(f"New K8 Integration ID: {integration_id}")

    else:
        response = requests.patch(f"{url}/{integration_id}", json=payload, headers=headers)
        print(f"Updated K8 Integration ID: {integration_id}")


    #TODO: wait for the integration to be ready
    print(f"Wating for integration {integration_id} to be ready")
    time.sleep(10) 

    url = f"https://api.us1.console.panoptica.app/api/kis/integrations/{integration_id}/helm-values"

    headers = {
        "accept": "text/plain",
        "Authorization": PANOPTICA_API_KEY
    }

    response = requests.get(url, headers=headers)
    
    if new_cluster:
        print(kustomize)
    
    print(base_tmpl.format(data=indent_text(response.text)))

if __name__ == "__main__":
    main()
