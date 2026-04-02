# Project 24: Encrypting and Decrypting Data using AWS KMS

> **Playlist:** [AWS Cloud LABS](https://www.youtube.com/playlist?list=PL6rbQ5F5xbtUDapCqcNV0srF8Uu-8RtSt)


## Introduction


**KMS** creates and stores **encryption keys** and performs **encrypt/decrypt** operations without exposing key material. This lab creates a **symmetric CMK**, separates **administrators** vs **users** of the key in IAM, and uses the **CLI** on EC2 with access keys to **encrypt** a file to ciphertext and **decrypt** it back—illustrating **envelope-style** thinking (data keys are internal; you pass plaintext/ciphertext to KMS APIs).


## Technologies and tools used


| Piece | Role |
|-------|------|
| **KMS key** | Logical key with ARN, alias, rotation settings. |
| **Symmetric encryption** | Same key encrypts and decrypts (most S3/EBS use cases). |
| **`aws kms encrypt` / `decrypt`** | CLI calls; ciphertext is base64-wrapped in CLI output. |


## Step-by-step lab walkthrough


<a href="https://youtu.be/M1-2kR5WXrs"><img src="https://github.com/user-attachments/assets/0955529d-1e92-4714-8494-fbd282e31bd3" width="720" height="400" /></a>

###

<img src="https://github.com/user-attachments/assets/b8130335-0014-4b17-b35f-e3e7045e48de" width="920" height="480" />

# Project 24: Encrypting and Decrypting Data using AWS KMS ✅

## **Overview**

- [ ] This project demonstrates how to use **AWS Key Management Service (KMS)** to encrypt, decrypt, and re-encrypt data securely.
- [ ] AWS KMS is a managed service that simplifies the creation and control of encryption keys, vital for protecting data at rest.
- [ ] You will:
  - [ ] Set up IAM groups and policies for KMS.
  - [ ] Create and manage users for encryption tasks.
  - [ ] Launch an EC2 instance to perform KMS operations using the AWS CLI.
  - [ ] Encrypt, decrypt, and re-encrypt files using an AWS KMS key.
- [ ] Key features of AWS KMS:
  - Hardware-based key storage and cryptographic operations.
  - Integrated logging with CloudTrail for compliance.
  - Strong separation of duties and credential protections.
  - Integration with other AWS services for secure key management.
  - Certified against SOC1, SOC2, SOC3, and PCI DSS level 1 standards.

## **Task 1: Sign in to AWS Management Console**

- [ ] Use your IAM **Username** and **Password** to sign in.
- [ ] Set the region to **US East (N. Virginia) us-east-1**.

## **Task 2: Create a User Group for KMS and Attach Policy**

- [ ] Navigate to **Services > IAM**.
- [ ] Go to **User groups** and click **Create group**.
- [ ] Set **Group name** to `KMSGroup`.
- [ ] For permissions, search for and attach the `KMS_Policy`.

<details>
  ```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": "kms:*",
      "Resource": "*"
    }
  ]
}
```

</details>

- [ ] Click **Create Group**.

## **Task 3: Create Two Users for Managing KMS**

- [ ] In **IAM**, go to **Users** and click **Create User**.
  - **User 1:** `KeyManager`
    - Check **Provide user access to the AWS Management Console**.
    - Password: `Mylabs@123`
    - Uncheck **User must create a new password at next sign-in**.
    - Add to group: `KMSGroup`
    - Complete creation and save user details.
    - Return to users list.
  - **User 2:** `KeyEncryption`
    - Check **Provide user access to the AWS Management Console**.
    - Password: `123@Mylabs`
    - Uncheck **User must create a new password at next sign-in**.
    - Add to group: `KMSGroup`
    - Complete creation and save user details.
    - Return to users list.
- [ ] For **KeyEncryption** user:
  - Go to **Security credentials** tab.
  - Click **Create access key**.
  - Select **Command Line Interface (CLI)** as use case, confirm, and click **Next**.
  - Skip description, click **Create access key**, and **Download .csv** file (save this for configuring AWS CLI).

## **Task 4: Create a KMS Key**

- [ ] Go to **Services > AWS Key Management Service (KMS)**.
- [ ] Click **Create a key**.
  - **Key type:** Symmetric
  - **Key usage:** Encrypt and decrypt
  - Click **Next**
  - **Alias:** `Admin`
  - Click **Next**
  - **Key administrative permissions:** Add `KeyManager`
  - Click **Next**
  - **Key usage permissions:** Add `KeyEncryption`
  - Click **Next**, review policy, and **Finish**.
- [ ] Copy the generated **Key ID** for later (save it in a text file).

## **Task 5: Launch an EC2 Instance**

- [ ] Go to **Services > EC2**.
- [ ] Click **Launch Instance**.
  - **Name:** `MyEC2Server`
  - **AMI:** Amazon Linux (from Quick Start)
  - **Instance type:** `t2.micro`
  - **Key pair:** Create `MyKey` (type: RSA, format: .pem)
  - Leave all settings as default.
- [ ] Click **Launch instance**.
- [ ] Wait for the instance to pass both status checks (**2/2 checks passed**).

## **Task 6: SSH into the EC2 Instance**

- [ ] Use your terminal or SSH client to connect (replace `ec2-user@<Public-IP>` and `MyKey.pem` as appropriate):
  ```bash
  ssh -i MyKey.pem ec2-user@<EC2-PUBLIC-IP>
  ```

## **Task 7: Perform KMS Encryption and Decryption**

- [ ] On your EC2 instance, create a file for encryption:
  ```bash
  echo "Welcome to Mylab" > secret.txt
  ```
- [ ] Configure AWS CLI with the **KeyEncryption** credentials:

  ```bash
  aws configure
  ```

  - Enter **AWS Access Key ID**, **Secret Access Key**, and region `us-east-1`.

- [ ] Encrypt the file using your KMS Key ID (replace `<replace-key-id>`):
  ```bash
  aws kms encrypt --key-id <replace-key-id> --plaintext fileb://secret.txt --output text --query CiphertextBlob | base64 --decode > encryptedsecret.txt
  ```
- [ ] View the encrypted content:
  ```bash
  cat encryptedsecret.txt
  ```
- [ ] Decrypt the file back to plaintext:
  ```bash
  aws kms decrypt --ciphertext-blob fileb://encryptedsecret.txt --output text --query Plaintext | base64 --decode > decryptedsecret.txt
  ```
- [ ] View the decrypted content:
  ```bash
  cat decryptedsecret.txt
  ```
- [ ] Re-encrypt the file again (replace `<replace-key-id>`):
  ```bash
  aws kms encrypt --key-id <replace-key-id> --plaintext fileb://decryptedsecret.txt --output text --query CiphertextBlob > newencryptedsecret.txt
  ```
- [ ] List all created files:
  ```bash
  ls -lrt
  ```
- [ ] View re-encrypted content:
  ```bash
  cat newencryptedsecret.txt
  ```

✅ Successfully encrypted, decrypted, and re-encrypted data using AWS KMS! 🎉


## Conclusion


You created **KMSGroup**, users **KeyManager** / **KeyEncryption**, a key **Admin**, and on EC2 ran **encrypt → decrypt → re-encrypt** on a sample file. **Security:** do not use weak shared passwords in production; use **IAM Identity Center** and **roles**. **CLI note:** `fileb://` reads binary; on **Windows** use **WSL** or **PowerShell** careful encoding if you replicate byte pipelines. Prefer **IAM roles on EC2** instead of long-term access keys when possible.
