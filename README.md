# Quantum Med Website

## Project is organised into 2 directories
- `terraform` - IaaC for website hosting
- `www` - source code for the website

---

## DNS Configuration
- Domain was bought at `ovhcloud.com`.
- The domain is delegated to the AWS DNS. There is a Route53 hosted zone created with a set of specific DNS entries.
- In `OVH panel` there was an external DNS configuration made that points to the servers from the Route53 hosted zone.
- From now on the domain is managed by AWS.

---

## Infrastructure

This project provisions a static website infrastructure using Terraform and AWS. Below is a list of components deployed:

- **S3 Bucket (`openmedgate-com`)**  
  Hosts the static files for the website. Public access is blocked; content is accessed securely via CloudFront.

- **ACM Certificate (in `us-east-1`)**  
  Provides SSL for `quantummed.eu` and `www.quantummed.eu`. Automatically validated via Route 53 DNS records.

- **CloudFront Distribution**  
  Serves the website globally over HTTPS with low latency. Connected to the private S3 bucket using Origin Access Control (OAC).

- **Route 53 DNS Records**  
  Two A-records point the domain (`openmedgate.com`) and subdomain (`www.quantummed.eu`) to the CloudFront distribution.

- **S3 Bucket Policy**  
  Grants CloudFront permission to read from the private S3 bucket using its unique `SourceArn`.

---

## Uploading changes to the server

As a prerequisite you need to install `aws-cli`. See this [link](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for details.

### AWS CLI profile
When using `aws-cli` for the first time. Run the below commands.

``
aws configure sso
``

You will be asked to provide the following details.

````
SSO session name (Recommended): quantummed-sso
SSO start URL [None]: https://d-99676a51bd.awsapps.com/start
SSO region [None]: eu-central-1
SSO registration scopes [sso:account:access]: 
CLI default client Region [None]: eu-central-1
CLI default output format [None]: json
CLI profile name [S3CloudFrontReadWriteAccess-483948415723]: quantummed-www-editor
````
**Note**: for `SSO registration scopes` just hit ENTER.

**Important**: Make sure you used `quantummed-www-editor` as the CLI profile name, because this name is used in the upload script.

### Before you update anything
Make sure you are updating the latest code base! Editing outdated content may result with **conflicts and generally troubles**. 
Before you start your work you need to `pull` latest changes from the repository. You can use this command to do so.

`git pull origin main`

### Publishing updated content
After you updated the website code you need to upload the changes to the AWS S3 bucket so that the
changes will be available in the Internet. To do this you just need to execute the below script.

`./upload_www_content.sh`

The script is triggering the `aws sso login` in case the session is not active. Then it synchronizes the `www` directory with the S3 bucket. 
Finally, it invalidates the CloudFront distribution cache, so that the changes are active right after invalidation (~1 minute).

### Commit your changes to the repository
After the changes were implemented you need to commit to the repository. We need to make sure the content we serve in the website
is what we store in the repository. **Not pushed changes may be dropped** in case somebody else edits outdated content and uploads it to the bucket. 
Also, it potentially causes troubles in merging conflicting changes.

The following commands can be used to commit changes.
````
git add .
git commit -m '<<<<< COMMENT DESCRIBING THE CHNAGES THAT WERE MADE >>>>>'
git push origin main
````
Now you are done. Great job!

---

## Access URLs

- `https://openmedgate.com`
