pulp_node_sync
==============

Trigger synchronization of "child" pulp node repositories upon modificationt of
parent pulp repository. Performs sync of repo when a message with subject:
"repo.publish.finish" is received on the ampq pulp exchange.

Inspired by Pulp v2's lack of node sync scheduling and a great pulp blog post
on the event amqp feature:

http://www.pulpproject.org/2012/11/02/amqp-notifications/


Tell Pulp to publish to AMQP upon completion of a repository "publish".

pulp-admin event listener amqp create --event-type repo.publish.finish --exchange pulp

