import boto3


def get_parameter(parameter_name, region_name='eu-central-1'):
    # Create a SSM client
    ssm_client = boto3.client('ssm', region_name=region_name)

    try:
        # Get the parameter
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        parameter_value = response['Parameter']['Value']
        return parameter_value
    except Exception as e:
        print(f"Error retrieving parameter: {e}")
        return None
