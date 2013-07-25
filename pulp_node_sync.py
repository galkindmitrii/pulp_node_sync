#!/usr/bin/env python
'''
Trigger synchronization of "child" pulp node repositories upon modificationt of
parent pulp repository. Performs sync of repo when a "repo.publish.finish"
subject message received on the ampq pulp exchange.

Inspired by Pulp v2's lack of node sync scheduling and a pulp blog post
on the event amqp feature: 

http://www.pulpproject.org/2012/11/02/amqp-notifications/
'''

import sys
import json
import argparse
import requests
from qpid.messaging import Connection

def get_args():

    desc = '''
    Trigger "child" pulp node repository synchronization upon receipt of a
    "repo.publish.finish" subject on the pulp exchange.'''

    example = '''
    Examples:

        pulp_node_sync.py -H localhost -P 5672 -u admin -p admin -e pulp
        pulp_node_sync.py --host localhost -exchange pulp
        '''

    parser = argparse.ArgumentParser( description = desc, epilog = example,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-H', '--host',
                        dest    = 'host',
                        default = 'localhost',
                        metavar = '',
                        help    = 'Hostname of parent pulp server')
    parser.add_argument('-P', '--port',
                        dest = 'port',
                        default = 5672,
                        metavar = '',
                        help = 'AMQP port number (default: 5672)')
    parser.add_argument('-u', '--user',
                        dest    = 'user',
                        default = 'admin',
                        metavar = '',
                        help    = 'Username to authenticate using (default: admin)')
    parser.add_argument('-p', '--password',
                        dest    = 'password',
                        default = 'admin',
                        metavar = '',
                        help    = 'Password to authenticate using (default: admin)')
    parser.add_argument('-e', '--exchange',
                        dest    = 'exchange',
                        default = 'pulp',
                        metavar = '',
                        help    = 'AMQP exchange (default: pulp)')
    args = parser.parse_args()
    return args


def get(relative_path):
    path = "https://%s/pulp/api/v2/%s" % (args.host, relative_path)
    r = requests.get(path, auth=(args.user,args.password), verify=False)
    return r.json()


def post(relative_path,body):
    path = "https://%s/pulp/api/v2/%s" % (args.host, relative_path)
    r = requests.post(path, auth=(args.user,args.password), verify=False, data=json.dumps(body))
    return r


def sync_node_repo(node_id, repo_id):
    ''' Schedules immediate synchronization of a given repo on a child node.
    Returns response body.'''
    body = {
        "units": [{
            "unit_key": { "repo_id": repo_id },
            "type_id": "repository"
            } ],
        "options": {}
        }
    path = "/consumers/%s/actions/content/update/" % node_id
    return post(path,body)


def get_nodes():
    " Returns list of child nodes (satelites)."
    consumers = get('/consumers/')
    return [ c['id'] for c in consumers if c['notes'].get('_child-node', False) ]


def get_nodes_repos(node):
    " Returns a child node's 'bound' repos."
    bindings = get("/consumers/%s/bindings/" % (node))
    return [ repo['repo_id'] for repo in bindings ]


if __name__ == '__main__':
    args = get_args()

    # qpid connection
    address = "%s:%s" % (args.host, args.port)
    receiver = Connection.establish(address).session().receiver(args.exchange)

    try:
        while True:
            message = receiver.fetch()
            json_message = json.loads(message.content)

            if json_message['payload']['result'] == 'success':
                repo_id = json_message['payload']['repo_id']
            else:
                continue

            nodes = get_nodes()
            for node in nodes:
                repos = get_nodes_repos(node)
                if repo_id in repos:
                    # trigger sync of that repo on child node
                    status = sync_node_repo(node,repo_id)
                    if status.status_code in range(200,299):
                        print("Triggered sync of %s on %s" % (repo_id, node))
                    continue

    except KeyboardInterrupt:
        pass
