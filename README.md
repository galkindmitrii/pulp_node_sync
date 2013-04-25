# pulp_node_sync

## Description

Trigger synchronization of "child" pulp node repositories upon modification of
parent pulp repository. Performs a sync of a repo when a message with subject:
"repo.publish.finish" is consumed on the ampq pulp exchange.

Inspired by Pulp v2's lack of node sync scheduling and a great pulp blog post
on the event amqp feature:

<http://www.pulpproject.org/2012/11/02/amqp-notifications/>

## Setup

Tell Pulp to publish to AMQP upon completion of a repository "publish".

<code>
pulp-admin event listener amqp create --event-type repo.publish.finish --exchange pulp
</code>

