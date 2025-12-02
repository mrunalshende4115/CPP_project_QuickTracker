import boto3

session = boto3.Session(region_name="us-east-1")
s3 = session.client('s3')
bucket_name = 'quicktrack-vehicle-docss'

#presigned url so that user can access for particular time 

def get_presigned_url(vehicle_id, doc_type, expires_in=3600):
    key = f"{vehicle_id}/{doc_type}.pdf"
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f" Failed to generate pre-signed URL for {key}: {e}")
        return None
        
#uploading my documents in S3

def upload_vehicle_docs(vehicle_id, reg_file, ins_file):
    reg_key = f"{vehicle_id}/registration.pdf"
    ins_key = f"{vehicle_id}/insurance.pdf"

    s3.upload_fileobj(reg_file, bucket_name, reg_key)
    s3.upload_fileobj(ins_file, bucket_name, ins_key)

    reg_url = f"https://{bucket_name}.s3.amazonaws.com/{reg_key}"
    ins_url = f"https://{bucket_name}.s3.amazonaws.com/{ins_key}"

    return reg_url, ins_url
