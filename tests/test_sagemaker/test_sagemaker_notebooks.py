import datetime

import boto3
from botocore.exceptions import ClientError
import pytest

from moto import mock_sagemaker
from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID

TEST_REGION_NAME = "us-east-1"
FAKE_SUBNET_ID = "subnet-012345678"
FAKE_SECURITY_GROUP_IDS = ["sg-0123456789abcdef0", "sg-0123456789abcdef1"]
FAKE_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/FakeRole"
FAKE_KMS_KEY_ID = "62d4509a-9f96-446c-a9ba-6b1c353c8c58"
GENERIC_TAGS_PARAM = [
    {"Key": "newkey1", "Value": "newval1"},
    {"Key": "newkey2", "Value": "newval2"},
]
FAKE_LIFECYCLE_CONFIG_NAME = "FakeLifecycleConfigName"
FAKE_DEFAULT_CODE_REPO = "https://github.com/user/repo1"
FAKE_ADDL_CODE_REPOS = [
    "https://github.com/user/repo2",
    "https://github.com/user/repo2",
]
FAKE_NAME_PARAM = "MyNotebookInstance"
FAKE_INSTANCE_TYPE_PARAM = "ml.t2.medium"


@pytest.fixture(name="client")
def fixture_sagemaker_client():
    with mock_sagemaker():
        yield boto3.client("sagemaker", region_name=TEST_REGION_NAME)


def _get_notebook_instance_arn(notebook_name):
    return f"arn:aws:sagemaker:{TEST_REGION_NAME}:{ACCOUNT_ID}:notebook-instance/{notebook_name}"


def _get_notebook_instance_lifecycle_arn(lifecycle_name):
    return (
        f"arn:aws:sagemaker:{TEST_REGION_NAME}:{ACCOUNT_ID}"
        f":notebook-instance-lifecycle-configuration/{lifecycle_name}"
    )


def test_create_notebook_instance_minimal_params(client):
    args = {
        "NotebookInstanceName": FAKE_NAME_PARAM,
        "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
        "RoleArn": FAKE_ROLE_ARN,
    }
    resp = client.create_notebook_instance(**args)
    expected_notebook_arn = _get_notebook_instance_arn(FAKE_NAME_PARAM)
    assert resp["NotebookInstanceArn"] == expected_notebook_arn

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert resp["NotebookInstanceArn"] == expected_notebook_arn
    assert resp["NotebookInstanceName"] == FAKE_NAME_PARAM
    assert resp["NotebookInstanceStatus"] == "InService"
    assert resp["Url"] == f"{FAKE_NAME_PARAM}.notebook.{TEST_REGION_NAME}.sagemaker.aws"
    assert resp["InstanceType"] == FAKE_INSTANCE_TYPE_PARAM
    assert resp["RoleArn"] == FAKE_ROLE_ARN
    assert isinstance(resp["LastModifiedTime"], datetime.datetime)
    assert isinstance(resp["CreationTime"], datetime.datetime)
    assert resp["DirectInternetAccess"] == "Enabled"
    assert resp["VolumeSizeInGB"] == 5


#    assert resp["RootAccess"] == True     # ToDo: Not sure if this defaults...


def test_create_notebook_instance_params(client):
    fake_direct_internet_access_param = "Enabled"
    volume_size_in_gb_param = 7
    accelerator_types_param = ["ml.eia1.medium", "ml.eia2.medium"]
    root_access_param = "Disabled"

    args = {
        "NotebookInstanceName": FAKE_NAME_PARAM,
        "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
        "SubnetId": FAKE_SUBNET_ID,
        "SecurityGroupIds": FAKE_SECURITY_GROUP_IDS,
        "RoleArn": FAKE_ROLE_ARN,
        "KmsKeyId": FAKE_KMS_KEY_ID,
        "Tags": GENERIC_TAGS_PARAM,
        "LifecycleConfigName": FAKE_LIFECYCLE_CONFIG_NAME,
        "DirectInternetAccess": fake_direct_internet_access_param,
        "VolumeSizeInGB": volume_size_in_gb_param,
        "AcceleratorTypes": accelerator_types_param,
        "DefaultCodeRepository": FAKE_DEFAULT_CODE_REPO,
        "AdditionalCodeRepositories": FAKE_ADDL_CODE_REPOS,
        "RootAccess": root_access_param,
    }
    resp = client.create_notebook_instance(**args)
    expected_notebook_arn = _get_notebook_instance_arn(FAKE_NAME_PARAM)
    assert resp["NotebookInstanceArn"] == expected_notebook_arn

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert resp["NotebookInstanceArn"] == expected_notebook_arn
    assert resp["NotebookInstanceName"] == FAKE_NAME_PARAM
    assert resp["NotebookInstanceStatus"] == "InService"
    assert resp["Url"] == f"{FAKE_NAME_PARAM}.notebook.{TEST_REGION_NAME}.sagemaker.aws"
    assert resp["InstanceType"] == FAKE_INSTANCE_TYPE_PARAM
    assert resp["RoleArn"] == FAKE_ROLE_ARN
    assert isinstance(resp["LastModifiedTime"], datetime.datetime)
    assert isinstance(resp["CreationTime"], datetime.datetime)
    assert resp["DirectInternetAccess"] == "Enabled"
    assert resp["VolumeSizeInGB"] == volume_size_in_gb_param
    #    assert resp["RootAccess"] == True     # ToDo: Not sure if this defaults...
    assert resp["SubnetId"] == FAKE_SUBNET_ID
    assert resp["SecurityGroups"] == FAKE_SECURITY_GROUP_IDS
    assert resp["KmsKeyId"] == FAKE_KMS_KEY_ID
    assert resp["NotebookInstanceLifecycleConfigName"] == FAKE_LIFECYCLE_CONFIG_NAME
    assert resp["AcceleratorTypes"] == accelerator_types_param
    assert resp["DefaultCodeRepository"] == FAKE_DEFAULT_CODE_REPO
    assert resp["AdditionalCodeRepositories"] == FAKE_ADDL_CODE_REPOS

    resp = client.list_tags(ResourceArn=resp["NotebookInstanceArn"])
    assert resp["Tags"] == GENERIC_TAGS_PARAM


def test_create_notebook_instance_invalid_instance_type(client):
    instance_type = "undefined_instance_type"
    args = {
        "NotebookInstanceName": "MyNotebookInstance",
        "InstanceType": instance_type,
        "RoleArn": FAKE_ROLE_ARN,
    }
    with pytest.raises(ClientError) as ex:
        client.create_notebook_instance(**args)
    assert ex.value.response["Error"]["Code"] == "ValidationException"
    expected_message = (
        f"Value '{instance_type}' at 'instanceType' failed to satisfy "
        "constraint: Member must satisfy enum value set: ["
    )

    assert expected_message in ex.value.response["Error"]["Message"]


def test_notebook_instance_lifecycle(client):
    args = {
        "NotebookInstanceName": FAKE_NAME_PARAM,
        "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
        "RoleArn": FAKE_ROLE_ARN,
    }
    resp = client.create_notebook_instance(**args)
    expected_notebook_arn = _get_notebook_instance_arn(FAKE_NAME_PARAM)
    assert resp["NotebookInstanceArn"] == expected_notebook_arn

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    notebook_instance_arn = resp["NotebookInstanceArn"]

    with pytest.raises(ClientError) as ex:
        client.delete_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert ex.value.response["Error"]["Code"] == "ValidationException"
    expected_message = (
        f"Status (InService) not in ([Stopped, Failed]). Unable to "
        f"transition to (Deleting) for Notebook Instance ({notebook_instance_arn})"
    )
    assert expected_message in ex.value.response["Error"]["Message"]

    client.stop_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert resp["NotebookInstanceStatus"] == "Stopped"

    client.list_notebook_instances()

    client.start_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert resp["NotebookInstanceStatus"] == "InService"

    client.stop_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)

    resp = client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert resp["NotebookInstanceStatus"] == "Stopped"

    client.delete_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)

    with pytest.raises(ClientError) as ex:
        client.describe_notebook_instance(NotebookInstanceName=FAKE_NAME_PARAM)
    assert ex.value.response["Error"]["Message"] == "RecordNotFound"


def test_describe_nonexistent_model(client):
    with pytest.raises(ClientError) as e:
        client.describe_model(ModelName="Nonexistent")
    assert e.value.response["Error"]["Message"].startswith("Could not find model")


def test_notebook_instance_lifecycle_config(client):
    name = "MyLifeCycleConfig"
    on_create = [{"Content": "Create Script Line 1"}]
    on_start = [{"Content": "Start Script Line 1"}]
    resp = client.create_notebook_instance_lifecycle_config(
        NotebookInstanceLifecycleConfigName=name, OnCreate=on_create, OnStart=on_start
    )
    expected_arn = _get_notebook_instance_lifecycle_arn(name)
    assert resp["NotebookInstanceLifecycleConfigArn"] == expected_arn

    with pytest.raises(ClientError) as e:
        client.create_notebook_instance_lifecycle_config(
            NotebookInstanceLifecycleConfigName=name,
            OnCreate=on_create,
            OnStart=on_start,
        )
    assert e.value.response["Error"]["Message"].endswith(
        "Notebook Instance Lifecycle Config already exists.)"
    )

    resp = client.describe_notebook_instance_lifecycle_config(
        NotebookInstanceLifecycleConfigName=name
    )
    assert resp["NotebookInstanceLifecycleConfigName"] == name
    assert resp["NotebookInstanceLifecycleConfigArn"] == expected_arn
    assert resp["OnStart"] == on_start
    assert resp["OnCreate"] == on_create
    assert isinstance(resp["LastModifiedTime"], datetime.datetime)
    assert isinstance(resp["CreationTime"], datetime.datetime)

    client.delete_notebook_instance_lifecycle_config(
        NotebookInstanceLifecycleConfigName=name
    )

    with pytest.raises(ClientError) as e:
        client.describe_notebook_instance_lifecycle_config(
            NotebookInstanceLifecycleConfigName=name
        )
    assert e.value.response["Error"]["Message"].endswith(
        "Notebook Instance Lifecycle Config does not exist.)"
    )

    with pytest.raises(ClientError) as e:
        client.delete_notebook_instance_lifecycle_config(
            NotebookInstanceLifecycleConfigName=name
        )
    assert e.value.response["Error"]["Message"].endswith(
        "Notebook Instance Lifecycle Config does not exist.)"
    )


def test_add_tags_to_notebook(client):
    args = {
        "NotebookInstanceName": FAKE_NAME_PARAM,
        "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
        "RoleArn": FAKE_ROLE_ARN,
    }
    resp = client.create_notebook_instance(**args)
    resource_arn = resp["NotebookInstanceArn"]

    tags = [
        {"Key": "myKey", "Value": "myValue"},
    ]
    response = client.add_tags(ResourceArn=resource_arn, Tags=tags)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    response = client.list_tags(ResourceArn=resource_arn)
    assert response["Tags"] == tags


def test_delete_tags_from_notebook(client):
    args = {
        "NotebookInstanceName": FAKE_NAME_PARAM,
        "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
        "RoleArn": FAKE_ROLE_ARN,
    }
    resp = client.create_notebook_instance(**args)
    resource_arn = resp["NotebookInstanceArn"]

    tags = [
        {"Key": "myKey", "Value": "myValue"},
    ]
    response = client.add_tags(ResourceArn=resource_arn, Tags=tags)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    tag_keys = [tag["Key"] for tag in tags]
    response = client.delete_tags(ResourceArn=resource_arn, TagKeys=tag_keys)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    response = client.list_tags(ResourceArn=resource_arn)
    assert response["Tags"] == []


def test_list_notebook_instances(client):
    for i in range(3):
        args = {
            "NotebookInstanceName": f"Name{i}",
            "InstanceType": FAKE_INSTANCE_TYPE_PARAM,
            "RoleArn": FAKE_ROLE_ARN,
        }
        client.create_notebook_instance(**args)

    client.stop_notebook_instance(NotebookInstanceName="Name1")

    instances = client.list_notebook_instances()["NotebookInstances"]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name0", "Name1", "Name2"]

    instances = client.list_notebook_instances(SortBy="Status")["NotebookInstances"]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name0", "Name2", "Name1"]

    instances = client.list_notebook_instances(SortOrder="Descending")[
        "NotebookInstances"
    ]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name2", "Name1", "Name0"]

    instances = client.list_notebook_instances(NameContains="1")["NotebookInstances"]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name1"]

    instances = client.list_notebook_instances(StatusEquals="InService")[
        "NotebookInstances"
    ]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name0", "Name2"]

    instances = client.list_notebook_instances(StatusEquals="Pending")[
        "NotebookInstances"
    ]
    assert [i["NotebookInstanceName"] for i in instances] == []

    resp = client.list_notebook_instances(MaxResults=1)
    instances = resp["NotebookInstances"]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name0"]

    resp = client.list_notebook_instances(NextToken=resp["NextToken"])
    instances = resp["NotebookInstances"]
    assert [i["NotebookInstanceName"] for i in instances] == ["Name1", "Name2"]
    assert "NextToken" not in resp
