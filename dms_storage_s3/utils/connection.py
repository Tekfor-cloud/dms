import boto3
import logging

from odoo import _, exceptions
from odoo.tools.config import config

from urllib.parse import urlsplit
from botocore.exceptions import ClientError, EndpointConnectionError

from slugify import slugify

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class BucketAlreadyExistsException(Exception):
    def __init__(self, bucket_name: str):
        return super().__init__(
            f"Bucket {bucket_name} already exists within your cloud provider"
        )


class NonEmptyBucketException(Exception):
    def __init__(self, bucket_name: str):
        return super().__init__(f"Bucket {bucket_name} is not empty")


class Connection:
    def __init__(self):
        host = config.get("aws_host")  # os.environ.get("AWS_HOST")

        # Ensure host is prefixed with a scheme (use https as default)
        if host and not urlsplit(host).scheme:
            host = "https://%s" % host

        self.region_name = config.get("aws_region")  # os.environ.get("AWS_REGION")
        access_key = config.get(
            "aws_access_key_id"
        )  # os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = config.get(
            "aws_secret_access_key"
        )  # os.environ.get("AWS_SECRET_ACCESS_KEY")

        params = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
        }

        if host:
            _logger.debug("aws_host %s", host)
            params["endpoint_url"] = host

        if self.region_name:
            params["region_name"] = self.region_name

        if not (access_key or secret_key):
            msg = _(
                "If you want to read from the S3 buckets, the following "
                "environment variables must be set:\n"
                "* AWS_ACCESS_KEY_ID\n"
                "* AWS_SECRET_ACCESS_KEY\n"
                "Optionally, the S3 host can be changed with:\n"
                "* AWS_HOST\n"
            )

            raise exceptions.UserError(msg)

        self._s3_resource = boto3.resource("s3", **params)
        _logger.debug("s3 resource = %s", self._s3_resource)
        self._s3 = self._s3_resource.meta.client

    def create_bucket(self, bucket_name) -> dict:
        exists = self._bucket_exists(bucket_name)
        if exists:
            raise BucketAlreadyExistsException(bucket_name)

        if self.region_name:
            return self._s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region_name},
            )
        return self._s3.create_bucket(Bucket=bucket_name)

    def _bucket_exists(self, bucket_name) -> bool:
        _logger.debug(self._s3._endpoint)
        _logger.debug("Test existence de %s", bucket_name)
        try:
            self._s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            _logger.exception("J'ai in client error")
            error_code = e.response["Error"]["Code"]
            _logger.debug("error code %s", error_code)
            if error_code == "404":
                return False
            raise exceptions.UserError(str(e))
        except EndpointConnectionError as error:
            # log verbose error from _s3, return short message for user
            _logger.exception("Error during connection on S3")
            raise exceptions.UserError(str(error)) from None
        return True

    def get_all_keys(self, bucket_name) -> list:
        for o in self._s3_resource.Bucket(bucket_name).objects.all():
            yield o.key

    def upload_fileobj(self, fd, bucket_name, key):
        # TODO : use put_object to store metadata (filename)
        return self._s3.upload_fileobj(fd, bucket_name, key)

    def download_fileobj(self, bucket_name, key, fd):
        # TODO : use get_object to store metadata (filename)
        return self._s3.download_fileobj(bucket_name, key, fd)

    def delete_objects(self, bucket_name: str, key_list):
        # delete_objects can delete up to 1000 objects at once, so we tokenize
        # key_list in 1000 item long chunks

        s3_limit = 1000
        key_list_2 = list(key_list)
        chunks = [
            key_list_2[i : i + s3_limit] for i in range(0, len(key_list_2), s3_limit)
        ]

        for chunk in chunks:
            self._s3.delete_objects(
                Bucket=bucket_name, Delete={"Objects": [{"Key": k} for k in chunk]}
            )

    def delete_bucket(self, bucket_name: str):
        r = self._s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        _logger.debug("list_objects_v2 response %s", r)
        if r["KeyCount"] > 0:
            raise NonEmptyBucketException(bucket_name)
        self._s3.delete_bucket(Bucket=bucket_name)


def get_bucket_name(storage_name: str, user_prefix=None) -> str:
    prefix = user_prefix or config.get("aws_bucket_prefix")
    if prefix:
        return slugify(f"{prefix} {storage_name}")
    return slugify(storage_name)
