
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/dms&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/dms/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/dms/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/dms/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/dms/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/dms/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/dms)
[![Translation Status](https://translation.odoo-community.org/widgets/dms-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/dms-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Document Management System modules for Odoo

OCA modules for DMS

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[dms](dms/) | 14.0.4.6.0 |  | Document Management System for Odoo
[dms_action](dms_action/) | 14.0.1.0.0 |  | Allow to add actions on DMS
[dms_field](dms_field/) | 14.0.1.0.0 |  | Create DMS View and allow to use them inside a record

[//]: # (end addons)

<!-- prettier-ignore-end -->


## DMS on S3 storage

### Python dependencies

The following dependencies should be present to use DMS S3 storages.

```text
boto3==1.26.7
python-slugify==8.0.4
```

### Configuration

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

### How to create the storage

Choose `S3` as `Save type` when creating a storage in Odoo. A bucket will then
be created on your object storage provider and associated with your storage.

### Particularities

* DMS storage's name is slugified to create the associated bucket.
* Bucket name unicity is checked before storage creation. The S3 user should therefore have the right to list buckets.
* Storage's `unlink` method deletes the associated bucket only if empty.


## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
