# Asset Service

## Commands
### Build
`docker build --no-cache -t assets:latest .`
### Create Version (patch)
`luma microservice-version add --from-version "*.*.*" --patch --docker-image assets:latest`
### Start Version
`luma microservice-version start`

## Ports
  Container Port = 5000

## Environment Variables
| Name  | Value |
| ------------- | ------------- |
| AWS_ACCESS_KEY_ID  | AWS Access Key Id Should only provide access to read / write to *BUCKET_NAME*  |
| AWS_SECRET_ACCESS_KEY  | AWS Secret Access Key  |
| BUCKET_NAME  | Name of AWS bucket that will store the assets  |

## Routes

### Route: /{path}

#### Call: GET

Purpose: Retrieve a file that has been uploaded to this service in the current experience.  The browser will need to have a the pwa_jwt cookie that is created by visiting an experience
