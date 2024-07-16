==========================================
Document Management System - Storage in S3
==========================================

Python dependencies
===================

The following dependencies should be present to use DMS S3 storages.

```text
boto3==1.26.7
python-slugify==8.0.4
```

Configuration
=============

Connection to S3 uses similar parameters to what is used by camptocamp's
[odoo-cloud-platform](/camptocamp/odoo-cloud-platform) addon:

* `AWS_HOST`: depends on the platform
* `AWS_REGION`: region's endpoint
* `AWS_ACCESS_KEY_ID`: depends on the platform
* `AWS_SECRET_ACCESS_KEY`: depends on the platform

We have added :

* `AWS_BUCKET_PREFIX`: prefix prepended to bucket name.

Connection can also be configured in `odoo.conf`, using the same keys in lowercase:

* `aws_host`
* `aws_region`
* `aws_access_key_id`
* `aws_secret_access_key`
* `aws_bucket_prefix`

How to create the storage
=========================

Choose `S3` as `Save type` when creating a storage in Odoo. A bucket will then
be created on your object storage provider and associated with your storage.

Particularities
===============

* DMS storage's name is slugified to create the associated bucket.
* Bucket name unicity is checked before storage creation. The S3 user should therefore have the right to list buckets.
* Storage's `unlink` method deletes the associated bucket only if empty.

Credits
=======

TEKFor
