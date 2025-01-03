from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import copy
import re
import logging
import sys


logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Output logs to stdout
    ],
)

logger = logging.getLogger("hawk-metactrl")





def new_dep(old):
    hawk = copy.deepcopy(old)
    hawk["spec"]["template"]

    hawk["metadata"]["labels"]["my-new"] = "metacontroller"

    return hawk


class Controller(BaseHTTPRequestHandler):
    def newIngress(self, parent: dict, children: dict) -> dict:
        return {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "Ingress",
    "metadata": {
 
        "name": parent['spec']['name'] + "-ingress",
        "namespace": "metacontroller"
 
    },
    "spec": {
        "rules": [
            {
                "host": "foo.bar.com",
                "http": {
                    "paths": [
                        {
                            "backend": {
                                "service": {
                                    "name": parent['spec']['name'] + "-svc",
                                    "port": {
                                        "number": 80
                                    }
                                }
                            },
                            "path": "/",
                            "pathType": "ImplementationSpecific"
                        }
                    ]
                }
            }
        ]
    }
}




    def newConfigMap(self, parent: dict, children: dict) -> dict:

        logger.info("This is NewConfigMap --- 04 ")
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "labels": parent['spec']['labels'],
                "name": parent['spec']['name'] + "-cm",
                "namespace": "metacontroller",
            },
            "data": {
                "nginx.conf": parent['spec']['nginxConfig']['value'] 
            },
        }


    def newService(self, parent: dict, children: dict) -> dict:

        logger.info("This is NewService --- 02 ")
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "labels": parent['spec']['labels'],
                "name": parent['spec']['name'] + "-svc",
                "namespace": "metacontroller",
            },
            "spec": {
                "internalTrafficPolicy": "Cluster",
                "ports": [{"port": 80, "protocol": "TCP", "targetPort": 80}],
                "selector": parent['spec']['labels'],
                "sessionAffinity": "None",
                "type": "ClusterIP",
            },
        }

    def newDeploy(self, parent: dict, children: dict) -> dict:
        desire_status = {}
        logger.info("This is SYNC --- 02 ")
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": parent['spec']['name'],
                "namespace": "metacontroller",
                "labels": parent['spec']['labels'],
            },
            "spec": {
                "replicas": parent['spec']['replicas'],
                "selector": parent['spec']['selector'],
                "template": {
                    "metadata": {"labels": parent['spec']['labels']},
                    "spec": {
                        "containers": [
                            {
                                "image": parent['spec']['image'],
                                "imagePullPolicy": "Always",
                                "name": parent['spec']['name'],

                "volumeMounts": [
                    {
                        "name": "nginx-config-volume",
                        "mountPath": "/etc/nginx/nginx.conf",
                        "subPath": "nginx.conf"
                    },
                ],


                                "resources": {},
                                "terminationMessagePath": "/dev/termination-log",
                                "terminationMessagePolicy": "File",
                            }
                        ],


        "volumes": [
            {
                "name": "nginx-config-volume",
                "configMap": {
                    "name": parent['spec']['name'] + "-cm"
                }
            },
        ],

                        "dnsPolicy": "ClusterFirst",
                        "restartPolicy": "Always",
                        "schedulerName": "default-scheduler",
                        "securityContext": {},
                        "terminationGracePeriodSeconds": 30,
                    },
                },
            },
        }

    def do_GET(self):
        logger.info("This is GET --- 00 ")

    def do_POST(self):
        logger.info("This is POST --- 01 ")

        observed = json.loads(self.rfile.read(int(self.headers.get("content-length"))))

        logger.info("This is POST --- 0101 ")

        logger.info("This is POST --- 0102--observed ")
        print(observed, file=sys.stdout)

        logger.info("This is POST --- 0103--parent ")
        print(observed["parent"], file=sys.stdout)

        parent = observed["parent"]
        children = observed["children"]

        logger.info("This is POST --- 0104--children ")
        print(observed["children"], file=sys.stdout)

        response: dict = {
            "status": {"working": "fine"},
            "children": [
                self.newConfigMap(parent, children),
                self.newDeploy(parent, children), 
                self.newService(parent, children), 
                self.newIngress(parent, children)],
        }

        print(response, file=sys.stdout)
        logger.info("This is POST --- 0106--response ")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))


logger.info("This is an info message")

# print("To start http svr !")
HTTPServer(("", 80), Controller).serve_forever()
