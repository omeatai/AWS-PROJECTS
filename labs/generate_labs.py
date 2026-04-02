"""
One-off generator: reads all-projects.md, extracts each project (handles nested <details>),
and writes N.md with Introduction, Technologies, walkthrough body, Conclusion.
Run from labs/: python generate_labs.py
"""
import re
from pathlib import Path

def extract_projects(text: str):
    lines = text.splitlines()
    projects = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r"<summary>Project (\d+) - (.+)</summary>", line)
        if m:
            j = i
            while j >= 0 and "<details>" not in lines[j]:
                j -= 1
            if j < 0:
                i += 1
                continue
            start = j
            depth = 0
            k = start
            body_lines = []
            while k < len(lines):
                ln = lines[k]
                opens = ln.count("<details>")
                closes = ln.count("</details>")
                if k == start:
                    depth = opens - closes
                    k += 1
                    continue
                depth += opens - closes
                if depth <= 0 and closes:
                    end_content = ln.replace("</details>", "").rstrip()
                    if end_content.strip():
                        body_lines.append(end_content)
                    break
                body_lines.append(ln)
                k += 1
            num, title = int(m.group(1)), m.group(2).strip()
            body = "\n".join(body_lines)
            projects.append((num, title, body))
            i = k + 1
            continue
        i += 1
    return projects


def fix_title(t: str) -> str:
    return t.replace("Lunch", "Launch").strip()


def clean_body(body: str) -> str:
    b = body.strip()
    while b.startswith("###\n\n"):
        b = b[4:].lstrip("\n")
    # Orphan tags left when stripping outer <details> from all-projects.md
    b = re.sub(r"<summary>.*?</summary>\s*", "", b, flags=re.DOTALL)
    b = b.replace("Lunch an EC2", "Launch an EC2").replace("Lunch ", "Launch ")
    # Remove empty heading markers left before video thumbnails
    lines = b.split("\n")
    while lines and lines[0].strip() == "###":
        lines = lines[1:]
        while lines and lines[0].strip() == "":
            lines = lines[1:]
    b = "\n".join(lines)
    return b.strip()


META = {
    1: {
        "intro": """Imagine the AWS account is a building: the **root user** holds the master key to everything. In real teams, almost nobody uses the root user for daily work. Instead, you create **IAM users** (individual logins) and **IAM groups** (teams), then attach **policies** that say what each group may do. This lab walks you through creating a console user, putting them in an **admin-style** group, and signing in as that user. You will see why AWS recommends **least privilege** (only the permissions someone needs)—here we use **AdministratorAccess** for learning; in production you would narrow that down.""",
        "tech": """| Tool | What it is (simple terms) |
|------|---------------------------|
| **AWS Management Console** | The website where you click to manage AWS. |
| **IAM (Identity and Access Management)** | Where you create users, groups, roles, and permissions. IAM is **global**—it does not belong to one Region. |
| **IAM user** | A named identity with its own password and/or access keys. |
| **IAM group** | A container you put users in; permissions attach to the group so many users share the same rules. |
| **Managed policy** | A pre-built permission document (like *AdministratorAccess*) that AWS maintains. |
| **Account alias** | A short name for your account so the sign-in URL is easier to remember than a 12-digit account ID. |""",
        "conclusion": """You created an IAM user with console access, placed the user in a new group, and attached **AdministratorAccess** to that group. You verified the user appears under **Users**, is a member of the group, and the group has the policy. Optionally you set an **account alias** and confirmed you can sign in as the IAM user in a private browser window. In practice, prefer **MFA** on privileged users and avoid sharing one admin user; this pattern is for learning how IAM ties users, groups, and policies together.""",
    },
    2: {
        "intro": """Policies are the **rules** of AWS: they are JSON documents that say *which API actions* are allowed or denied on *which resources*. AWS ships hundreds of **managed policies** (for example *IAMReadOnlyAccess*). This lab helps you read those policies and build a **custom policy** that only allows a few IAM read actions—good practice for **least privilege**.""",
        "tech": """| Tool | What it is |
|------|------------|
| **IAM Policies** | JSON (or visual editor) that lists `Effect`, `Action`, `Resource`, and optional `Condition`. |
| **Managed policy** | AWS-maintained policy you attach as-is (e.g. *AdministratorAccess*, *IAMReadOnlyAccess*). |
| **Custom policy** | A policy you author for your own needs. |
| **Visual editor / JSON** | Two ways to build policies in the IAM console; both produce the same underlying policy document. |""",
        "conclusion": """You inspected existing managed policies (including their JSON) and created a custom policy allowing specific IAM read actions (such as listing and describing users). You now understand that permissions are explicit: if an action is not allowed in the policy, AWS denies it. Next steps in real environments: test with the **Policy Simulator**, use **permissions boundaries** for delegated admin, and prefer **managed** or **customer-managed** policies over inline policies for reuse.""",
    },
    3: {
        "intro": """The **AWS CLI** lets you control AWS from a terminal (scripting, automation, and faster workflows). **AWS CLI v2** is the current major version for Windows, macOS, and Linux. This lab installs it on Windows and checks the install with `aws --version`.""",
        "tech": """| Tool | What it is |
|------|------------|
| **AWS CLI v2** | Command-line program that talks to AWS APIs. |
| **MSI installer** | Windows installer from AWS ([AWS CLI install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))—use the official page for the current MSI link. |
| **Command Prompt / PowerShell / Windows Terminal** | Shells where you run `aws` commands. |""",
        "conclusion": """You downloaded the official **AWS CLI v2** MSI for Windows, ran the installer, and confirmed `aws --version` reports **aws-cli/2**. With the CLI installed, you can later run `aws configure` (after creating access keys in IAM) to call services without opening the browser. On **Windows 11**, you can alternatively run `winget install -e --id Amazon.AWSCLI`, then open a **new** terminal and verify with `aws --version`. **Windows Terminal** is nicer than legacy Command Prompt for daily use.""",
        "extra_steps_note": """
### Optional: install with winget (Windows 10/11)

If you prefer a package manager: open **Terminal** or **PowerShell** and run `winget install -e --id Amazon.AWSCLI`, then close and reopen the terminal and run `aws --version`. The MSI method in the video matches the step-by-step instructions in the [AWS CLI User Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
""",
    },
    4: {
        "intro": """Access keys are **long-term credentials** (Access Key ID + Secret Access Key) used by the CLI, SDKs, and tools. AWS now **strongly prefers** temporary credentials via **IAM Identity Center (SSO)** or **IAM roles**, but access keys are still common in tutorials. Here you create keys for a user, run `aws configure`, test with `aws iam list-users`, then prove that **removing the user from an admin group** immediately removes CLI power—showing that permissions come from policies, not from the keys alone.""",
        "tech": """| Tool | What it is |
|------|------------|
| **Access keys** | Static credentials for programmatic access; treat the secret like a password—never commit it to Git. |
| **`aws configure`** | Stores default region, output format, and credentials in a profile (under `~/.aws/`). |
| **IAM groups & policies** | Removing a user from a group that had admin policies revokes those permissions. |""",
        "conclusion": """You created access keys, configured the CLI, verified `list-users` worked, removed the user from the admin group, saw the CLI lose permission, then restored access by adding the user back. **Takeaway:** rotate or delete unused keys; use **IAM Identity Center** or **roles** where possible; never share or upload `.csv` key files. For new work, consider **`aws configure sso`** instead of long-term keys.""",
    },
    5: {
        "intro": """An **IAM role** is an identity that **AWS services** or **people** can *assume* temporarily. For EC2, you attach a **instance profile** (wrapper around a role) so the instance can call AWS APIs **without** embedding access keys on disk. This lab creates a role that EC2 can assume with **IAMReadOnlyAccess**—a small, safe permission for demos.""",
        "tech": """| Tool | What it is |
|------|------------|
| **IAM role** | Identity with policies + a **trust policy** (who may assume the role). |
| **Trust policy** | JSON saying *which principal* can use the role (here: EC2 service). |
| **EC2 instance profile** | Lets an EC2 instance assume the attached role automatically. |
| **IAMReadOnlyAccess** | Read-only IAM API access—useful for demos, not for app secrets. |""",
        "conclusion": """You created a role trusted by **EC2**, attached **IAMReadOnlyAccess**, and named it (for example *DemoRoleForEC2*). In a follow-on lab you would launch an instance with this role and use **instance metadata** or the AWS CLI on the box to verify calls work. **Security note:** grant only the permissions the application needs (e.g. `s3:GetObject` on one bucket), not broad IAM read on production systems unless required.""",
    },
    6: {
        "intro": """Good security is not only *strong passwords*—it is also **visibility**. AWS IAM can generate a **credential report** (CSV) for every user in the account and show **when permissions were last used** (Access Advisor / “Last accessed”). This lab uses those tools to spot stale passwords, missing MFA, and unused services—classic audit tasks.""",
        "tech": """| Tool | What it is |
|------|------------|
| **Credentials report** | Account-wide CSV: password enabled, key rotation, MFA status, etc. |
| **Access Advisor / Last accessed** | Per-user or per-role view of which services were touched and when. |
| **MFA** | Second factor for sign-in; the report shows if it is on. |""",
        "conclusion": """You downloaded and read the credential report and used per-user **last accessed** data to see which services permissions actually touched. Use this in real life to **right-size** policies: if a user never used a service, consider removing that permission. Combine with **organizations SCPs**, **password policy**, and **MFA enforcement** for stronger baseline security.""",
    },
    7: {
        "intro": """**EC2** is a virtual server in the cloud. This lab launches a small **Amazon Linux** instance in the **default VPC**, opens **SSH** (manage) and **HTTP** (web), and uses **user data**—a script that runs **once** at first boot—to install **Apache (httpd)** and serve a simple HTML page. You then open the site in a browser using the instance **public IPv4** address.""",
        "tech": """| Tool | What it is |
|------|------------|
| **EC2** | Elastic Compute Cloud—virtual machines (instances). |
| **AMI** | Template image for the OS (e.g. Amazon Linux 2023 or Amazon Linux 2). |
| **Security group** | Virtual firewall rules for the instance (ports/sources). |
| **Key pair** | SSH key: you keep the `.pem` private key; AWS puts the public key on the instance. |
| **User data** | Shell script or cloud-init directives run at launch (great for bootstrapping). |
| **Apache httpd** | Web server serving pages on port 80. |""",
        "conclusion": """You launched an EC2 instance with a security group allowing SSH and HTTP, used **user data** to install **httpd** and write `index.html`, and verified the page in a browser with `http://` and the public IP. You practiced **stop/start** to save money when not using the instance. **Updates (2026):** the console often defaults to **Amazon Linux 2023**; package installs use **`dnf`** instead of **`yum`**. If you pick AL2023, replace `yum` with `dnf` in user data (see note under *Technologies*). Free tier limits still apply where your account is eligible.""",
        "extra_steps_note": """
### Note for Amazon Linux 2023 (recommended today)

If your AMI is **Amazon Linux 2023**, use this user data instead of `yum`:

```bash
#!/bin/bash
dnf update -y
dnf install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Hello World from $(hostname -f)</h1>" > /var/www/html/index.html
echo "<p>Created by your lab</p>" >> /var/www/html/index.html
```

Amazon Linux 2 still supports `yum`; both are valid for learning.
""",
    },
    8: {
        "intro": """A **VPC** is your private network in AWS. The **default VPC** makes first launches easy; this lab **recreates** the default VPC (delete + create default) so you see where it lives, then launches **Amazon Linux 2** in that VPC, connects with **EC2 Instance Connect**, installs **httpd** manually, and serves a simple page. You practice the full path from network to web server without user data automation.""",
        "tech": """| Tool | What it is |
|------|------------|
| **VPC** | Isolated IP network; subnets, routing, internet gateway. |
| **Default VPC** | Pre-made VPC per Region with a public subnet in each AZ. |
| **EC2 Instance Connect** | Browser-based SSH using temporary keys (no local `ssh` required). |
| **Security group** | Controls inbound/outbound traffic to the instance. |""",
        "conclusion": """You reset the **default VPC**, launched **MyEC2Server** with HTTP+SSH access, used **EC2 Instance Connect** to get a shell, installed and started **httpd**, and viewed your HTML in the browser. **Modern option:** Amazon Linux 2023 uses `dnf` instead of `yum` for package install. Deleting the default VPC is **destructive**—only do this in a sandbox account; production accounts rarely delete the default VPC without planning.""",
    },
}

# Fill remaining projects 9-25 with concise meta (full walkthrough stays from extract)
REST = {
    9: ("""This lab builds **high availability**: an **Application Load Balancer (ALB)** spreads HTTP traffic across instances in multiple **Availability Zones**, while an **Auto Scaling group** replaces unhealthy instances and scales on **CPU**. You create **security groups** so only the load balancer talks HTTP to the app servers, a **launch template** with **user data** to install Apache, a **target group** with a health check path, then wire the ALB and ASG together.""",
         """| Component | Role |
|-----------|------|
| **ALB** | Layer-7 load balancer; checks **health** before sending traffic. |
| **Target group** | List of instances (or IPs) the ALB forwards to. |
| **Auto Scaling** | Keeps **desired capacity**; replaces failed instances; can scale on metrics. |
| **Launch template** | Reusable launch spec (AMI, type, SG, user data). |
| **Security groups** | LB accepts internet HTTP; instances accept HTTP **only** from the LB SG. |""",
         """You deployed a small **two-tier pattern**: public load balancer, private-ish app tier (HTTP from LB only), ASG **desired capacity 2**, **target tracking** on CPU, and verified failover by stopping an instance. You cleaned up ASG, template, LB, and target group to avoid charges. **Tip:** health check path `/health.html` must exist (your user data creates it). **Cost:** NAT is not used here; ALB and EC2 still incur charges outside free tier."""),
    10: ("""**S3** stores objects (files). **Lambda** runs code without servers you manage. This lab triggers Lambda when a new object lands in a **source** bucket; the function copies the object to a **destination** bucket using **boto3**. You see **event-driven architecture**: upload → event → Lambda → copy.""",
         """| Service | Role |
|---------|------|
| **S3** | Object storage; event notifications can invoke Lambda. |
| **Lambda** | Python 3.x runtime; execution role needs `s3:GetObject` on source and `s3:PutObject` on destination. |
| **IAM role (Lambda execution)** | The lab references `Lambda_role`—create a role with trust `lambda.amazonaws.com` and S3 permissions, or use the console wizard. |
| **CloudWatch Logs** | Lambda writes logs here for debugging. |""",
         """You created two buckets, a Lambda with **S3 trigger** on object create, and verified the copy. **Important:** If you do not have `Lambda_role`, use **Create function** → **Change default execution role** → **Create a new role with basic Lambda permissions**, then **add** an inline policy or attach policies for `s3:GetObject` (source ARN) and `s3:PutObject` (dest ARN). Enable **recursive invocation** only if you understand loop risk (copying back to source). Replace placeholder bucket names in code. **Python 3.13** is fine if offered; otherwise pick the newest Python runtime in the console."""),
    11: ("""Organizations split work by team. IAM **groups** let you attach the same policies to many **users**. Here you create **Dev** users with read-only EC2/S3 and **HR** users with **billing** access, tagged for clarity—mirroring how real companies structure console access.""",
         """| Concept | Use |
|---------|-----|
| **IAM users** | John, Sarah, Ted, Rita with tags `Dev-Team` / `HR-Team`. |
| **Groups** | `Dev-Team` → `AmazonEC2ReadOnlyAccess` + `AmazonS3ReadOnlyAccess`; `HR-Team` → billing-related policy. |
| **Tags** | Metadata for cost and organization (optional but good practice). |""",
         """You created four users, two groups, attached **managed policies**, and placed users in the right groups. **Security reminder:** use strong unique passwords or **MFA**; the sample password in videos is for sandboxes only. **Billing** access should be limited to people who truly need it; consider **IAM policy conditions** and **AWS Organizations** for enterprise billing roles."""),
    12: ("""This is the classic **custom VPC** layout: one **public** subnet (routes to the internet via **Internet Gateway**) and one **private** subnet (no direct internet route in this lab). You create the VPC, subnets, IGW, and **route tables** so only the public subnet reaches `0.0.0.0/0` through the IGW. Private subnets here are “private” at the routing level—apps in them cannot browse the web until you add **NAT Gateway** (next lab).""",
         """| Resource | Purpose |
|----------|---------|
| **VPC** | `10.0.0.0/16` private address space. |
| **Subnet** | Slice of the VPC CIDR per AZ (`10.0.1.0/24` public, `10.0.2.0/24` private in original lab). |
| **Internet Gateway** | VPC attachment for public internet routing. |
| **Route tables** | Associate subnets; public table has `0.0.0.0/0` → IGW. |""",
         """You built **MyVPC** with **MyPublicSubnet** and **MyPrivateSubnet**, attached an IGW, and split **PublicRouteTable** vs **PrivateRouteTable** with correct associations. The private subnet has **no default route to the internet**—that is intentional. Next lab adds **NAT** for outbound-only internet from private instances. Double-check **CIDRs** do not overlap if you peer or connect to on-premises networks later."""),
    13: ("""Private instances often need **outbound** internet (updates, package installs) without giving them **public IPs**. A **NAT Gateway** in a **public** subnet, plus a **route** in the **private** route table (`0.0.0.0/0` → NAT), provides that. NAT is **managed** (AWS patches it) but **costs money** (hourly + data). This lab also shows **SSH jump** via a public instance to reach a private instance.""",
         """| Resource | Purpose |
|----------|---------|
| **NAT Gateway** | Outbound internet for private subnets; needs an **Elastic IP** in public subnet. |
| **Elastic IP** | Static public IPv4 for the NAT GW. |
| **Bastion-style SSH** | SSH to public instance, then SSH to private using private key on the bastion (sandbox pattern). |""",
         """You confirmed the private instance could not `yum update`, created a **NAT Gateway** and added **`0.0.0.0/0` → NAT** on the **private** route table (the lab uses **Main** route table—verify your private subnet is associated with the table you edited). After NAT, updates succeed. **Note:** The original lab duplicates a heading “SSH into MyPublicServer”; follow the steps in order. **Security:** restrict SSH sources in production; prefer **SSM Session Manager** over `0.0.0.0/0` SSH."""),
    14: ("""**Security groups** are **stateful** firewalls at the **ENI** (instance) level. **Network ACLs** are **stateless** filters at the **subnet** edge—both must allow traffic for it to flow. This lab builds a small VPC, SG rules (SSH + ICMP), custom **NACL** rules, launches public/private instances, and **pings** across subnets to see layers working together.""",
         """| Control | Layer |
|---------|-------|
| **Security group** | Instance; stateful; allow SSH and ICMP from needed sources. |
| **NACL** | Subnet; stateless; need matching inbound **and** outbound ephemeral rules for return traffic. |
| **ICMP** | Ping; useful for network debugging (often blocked in hardening). |""",
         """You deployed **my_VPC** with public/private subnets, routing, **my_securitygroup**, **my_NACL** attached to both subnets, and verified **ping** from the public to the private instance. **Lesson:** overlapping SG + NACL means **most restrictive** effective path can block traffic—when ping fails, check **both**. Production tip: avoid SSH from `0.0.0.0/0`; use **Session Manager** or a locked-down bastion. PuTTY steps in the original still work; Windows 10+ includes **OpenSSH** client natively."""),
    15: ("""**Infrastructure as Code** means describing AWS resources in a file (**template**) and letting **CloudFormation** create/update/delete them as a **stack**. This lab deploys a sample **LAMP** stack (Linux, Apache, MySQL, PHP) on one **EC2** instance using **`cfn-init`** in user data. The template lives in **S3**; the stack parameters pass DB passwords and key name.""",
         """| Tool | Role |
|------|------|
| **CloudFormation** | Declarative provisioning; tracks resources as a stack. |
| **S3** | Hosts the template JSON URL. |
| **cfn-init / cfn-signal** | Bootstrap instance and signal success/failure to CloudFormation. |
| **Parameters / Mappings** | Template inputs and Region→AMI mapping. |""",
         """You (or the video) uploaded **LAMP_template.json** to S3, created a stack **MyFirstCFStack**, waited for **CREATE_COMPLETE**, and opened the **WebsiteURL** output. **Critical update:** sample templates often pin **old AMI IDs** in `Mappings`. Before deploying in 2026, **replace the AMI** in the mapping with a current **Amazon Linux 2** AMI ID for your Region (EC2 → AMIs → search AL2). Old AMIs may be retired. The template uses **legacy PHP/mysql APIs**—fine for lab history; new apps use **PDO** and supported MySQL versions. Always **delete stacks** when finished to stop EC2 billing."""),
    16: ("""You deploy a **VPC** entirely from CloudFormation: first a template with **two subnets** (public + private) and routing, then **update the stack** with a second template that adds **second AZ** subnets. This shows **stack updates** and how IaC stays the **source of truth** for network layout.""",
         """| Concept | Use |
|---------|-----|
| **VPC, IGW, subnets, route tables** | Defined as `AWS::EC2::*` resources. |
| **`Fn::GetAZs` / `Fn::Select`** | Pick AZs without hard-coding names. |
| **Stack update** | Replace template to add subnets across AZs. |""",
         """You created **MyStack123** from **VPC_template.json**, verified resources, then **updated** the stack with **VPC_II_template.json** and confirmed **four** subnets in the VPC console. **Gotcha:** updating networking in place can fail if resources conflict—use a lab account. Prefer **YAML** for new templates (readability); JSON is still valid. Outputs expose **VPC ID** and **AZ** names for follow-on stacks."""),
    17: ("""**VPC Flow Logs** capture **IP traffic** metadata (accept/reject, src/dst, ports) for visibility and forensics. This lab sends flow logs to **CloudWatch Logs** so you can search and retain them. You need an **IAM role** that allows VPC Flow Logs to **publish** to the log group.""",
         """| Service | Role |
|---------|------|
| **CloudWatch Logs** | Stores log events in **log groups** / **streams**. |
| **Flow Logs** | Can target CloudWatch, S3, or Kinesis. |
| **IAM role** | `vpc-flow-logs.amazonaws.com` service role with `logs:CreateLogStream`, `PutLogEvents`, etc. |""",
         """You created log group **myvpclogs**, VPC **myvpc**, and a flow log filtered to **Accepted** traffic (you can also choose **All** or **Rejected**). **Modern shortcut:** the console can **create the IAM role** automatically when you pick CloudWatch Logs—use that unless you need a custom policy. Flow logs cost **per GB** ingested; set **retention** on the log group. For central security analytics, many teams also send copies to **S3** or **Security Lake**."""),
    18: ("""Private subnets without NAT cannot reach the **public S3 API** on the internet—but you can reach S3 privately using a **Gateway VPC Endpoint** (free, **route-table** based). Combined with a **bastion** (jump host) for SSH, you can manage a private instance and still use **AWS CLI** to list buckets **without** a NAT Gateway.""",
         """| Piece | Role |
|-------|------|
| **Gateway endpoint (S3)** | Adds prefix routes in the route table to Amazon S3 over the AWS network. |
| **Bastion host** | Public instance you SSH into, then SSH to private. |
| **Security groups** | Bastion allows SSH from your IP (best) or anywhere (lab only); private allows SSH from bastion SG. |""",
         """You built a small VPC, bastion + private instance, and an **S3 gateway endpoint** on the **private** route table. **Fix to know:** listing S3 with CLI from the private instance still needs **credentials** (instance role or keys on the instance); the endpoint provides **network path**, not identity. The original lab runs `aws configure` on the bastion—move toward **IAM instance profiles** and **`aws sts get-caller-identity`** checks. **CIDR math:** `192.168.0.1/27` in the source doc is unusual; typical subnets use network addresses like `192.168.0.0/27`—in the console, pick valid subnet CIDRs inside your VPC range."""),
    19: ("""**Transit Gateway (TGW)** is a **hub** that connects many VPCs (and optionally on-premises) with one place to manage routing. This lab builds **two VPCs**, a public server in one and a private server in the other, attaches both VPCs to a TGW, adds **routes** so `10.0.0.0/24` and `20.0.0.0/24` talk through the TGW, then SSHs from the public side to the private instance. The embedded JSON policy in the source is a **classroom-scoped** example—use **least privilege** in real life.""",
         """| Piece | Role |
|-------|------|
| **Transit Gateway** | Regional hub; attachments per VPC. |
| **TGW route tables** | Control which attachments can reach which CIDRs (advanced labs). |
| **VPC attachments** | Connect each VPC to the TGW. |
| **EC2 / Session Manager** | Alternative to SSH when SSM agent + IAM role are configured. |""",
         """You enabled DNS hostnames/resolution on both VPCs, created subnets and a public route to IGW in the first VPC, launched instances, created **DemoTG** and **two VPC attachments**, added static routes on each VPC’s relevant route tables toward the other CIDR via **Transit Gateway**, and tested SSH from **First_VPCs_EC2** to the private IP of **Second_VPCs_EC2**. **Simpler alternative for two VPCs only:** **VPC peering** (no TGW). Use **TGW** when you have **many** VPCs or hybrid cloud. **Cost:** TGW has hourly and data processing charges—tear down after the lab."""),
    20: ("""**GuardDuty** is a **threat detection** service that analyzes CloudTrail, VPC Flow Logs, and DNS logs (depending on configuration) to surface **findings** (suspicious API usage, crypto mining patterns, etc.). This lab turns it on, tours settings and optional **trusted/threat IP lists**, and generates **sample findings** to learn the UI.""",
         """| Area | Meaning |
|------|---------|
| **Detector** | GuardDuty resource per Region (enable/disable per Region). |
| **Findings** | Structured issues with severity; can feed **Security Hub** / **EventBridge**. |
| **Lists** | Trusted IP (allow) and threat IP (block) customization. |""",
         """You enabled GuardDuty, explored **Settings**, **Lists**, and **Accounts** (for multi-account), and generated **sample findings** to practice triage. **Operational tip:** enable GuardDuty in **each Region** you use (or automate with **Organizations**). **Cost:** charged per analyzed volume; sample findings are safe demos. Connect to **Security Hub** for a single pane of glass."""),
    21: ("""**Amazon Macie** discovers **sensitive data** in **S3** using **managed data identifiers** (e.g. credentials patterns) and **custom data identifiers** (your regex). This lab enables Macie, runs a **one-time job** over a bucket (CSV focus), and reviews **findings**.""",
         """| Piece | Role |
|-------|------|
| **Macie** | S3-focused data security / privacy scanning. |
| **Managed identifiers** | Prebuilt detectors for many PII types. |
| **Custom identifier** | Regex like `[a-z]{2}-[0-9]{2}` for your pattern. |
| **Job** | One-time or scheduled scope over selected buckets. |""",
         """You enabled Macie, created **myIdentifier**, ran job **myJob** against a bucket, and exported findings. **Prerequisites:** Macie needs **appropriate permissions** and buckets in **supported Regions**. For cost control, scope jobs to **prefixes** and limit **file types**. Macie complements **Macie for IAM** (different product area)—this lab is **S3 data** classification."""),
    22: ("""**AWS WAF** filters HTTP/HTTPS at the edge of **Application Load Balancer**, **API Gateway**, etc. This lab pairs **security groups** (network ACL–like at instance/LB) with **WAF Web ACLs** (Layer 7 rules). You shrink the LB SG to only your IP/bastion, then add a WAF **IP set** rule to **block** even that IP—seeing layered controls.""",
         """| Tool | Role |
|------|------|
| **ALB** | Spreads traffic to two Apache servers with distinct pages. |
| **Security group** | IP allow list at the LB (coarse). |
| **WAF Web ACL + IP set** | Block/allow at application layer (fine, rule-based). |""",
         """You built two web servers, an ALB + target group, a bastion, verified round-robin, locked the **LB security group** to bastion IP (browser from home stops working; `curl` from bastion works), then attached a **WAF** rule blocking that IP to get **403**. **Console name (2026):** use **AWS WAF** (can be “WAF & Shield” in older docs). **Best practice:** keep **SSH** off `0.0.0.0/0`; use **prefix lists** or **your `/32` IP** on the LB when testing."""),
    23: ("""You extend the ALB + two-server pattern with **AWS WAF managed rule groups** to block common attacks: **SQLi** patterns, **geo** restrictions, and **query string** rules. Managed rules are maintained by AWS and partners; you tune with **count** mode first in production before **block**.""",
         """| Piece | Role |
|-------|------|
| **ALB + target group** | Same as prior lab backbone. |
| **Web ACL** | Regional (ALB) association. |
| **Managed rule groups** | Prebuilt signatures; names in console change over time—search “SQL”, “Geo”, “Known bad inputs”. |""",
         """You stood up servers and an ALB, confirmed traffic, then attached a Web ACL with managed groups. **Update for 2026:** exact rule **group names** in the console evolve (e.g. **Core rule set**, **SQL database**, **Anonymous IP list**). Use **Add rules** → **Add managed rule groups** and search keywords (**SQL**, **geo match**, **query string**). Test with sample malicious URLs from the lab; expect **403** or **CAPTCHA** depending on rule action. Start with **Count** to avoid breaking legitimate traffic."""),
    24: ("""**KMS** creates and stores **encryption keys** and performs **encrypt/decrypt** operations without exposing key material. This lab creates a **symmetric CMK**, separates **administrators** vs **users** of the key in IAM, and uses the **CLI** on EC2 with access keys to **encrypt** a file to ciphertext and **decrypt** it back—illustrating **envelope-style** thinking (data keys are internal; you pass plaintext/ciphertext to KMS APIs).""",
         """| Piece | Role |
|-------|------|
| **KMS key** | Logical key with ARN, alias, rotation settings. |
| **Symmetric encryption** | Same key encrypts and decrypts (most S3/EBS use cases). |
| **`aws kms encrypt` / `decrypt`** | CLI calls; ciphertext is base64-wrapped in CLI output. |""",
         """You created **KMSGroup**, users **KeyManager** / **KeyEncryption**, a key **Admin**, and on EC2 ran **encrypt → decrypt → re-encrypt** on a sample file. **Security:** do not use weak shared passwords in production; use **IAM Identity Center** and **roles**. **CLI note:** `fileb://` reads binary; on **Windows** use **WSL** or **PowerShell** careful encoding if you replicate byte pipelines. Prefer **IAM roles on EC2** instead of long-term access keys when possible."""),
    25: ("""End-to-end **encryption** practice: **SSE-KMS** on **S3**, **key rotation**, **cross-region replication (CRR)** to a second bucket (Mumbai) with encryption handling, **disable key** to see access break, then **EBS** volume and **AMI copy** encryption with the same customer managed key mindset.""",
         """| Piece | Role |
|-------|------|
| **SSE-KMS** | S3 uses KMS to encrypt objects; callers need decrypt permission. |
| **CRR** | Async copy across Regions; needs **versioning**, **IAM role**, and compatible encryption settings. |
| **EBS encryption** | Volume encrypted under a KMS key you choose. |
| **AMI copy** | Can encrypt snapshots on copy with a new key. |""",
         """You created **Mykey**, enabled **rotation**, built **Mysource123** with default SSE-KMS, uploaded an object, proved **public URL** fails while **Open** in console works (authorized decrypt), configured **replication** to **ap-south-1**, tested **key disable** (access denied), re-enabled, created encrypted **EBS**, and **copied AMI** with encryption. **Updates:** S3 **Object Ownership** defaults changed over time—**ACLs disabled** is common now; “make public using ACL” may not apply; use **bucket policy** carefully if you truly need public reads (usually avoid). **Replication** IAM role must allow **kms:Decrypt** on source key and **encrypt** on destination. Clean up buckets, keys (schedule deletion), volumes, and snapshots to avoid cost."""),
}

for n in range(9, 26):
    META[n] = {"intro": REST[n][0], "technologies": REST[n][1], "conclusion": REST[n][2]}

# Rename legacy "tech" key to "technologies" for projects 1–8
for k in list(META.keys()):
    if "technologies" not in META[k] and "tech" in META[k]:
        META[k]["technologies"] = META[k].pop("tech")


def main():
    root = Path(__file__).parent
    text = (root / "all-projects.md").read_text(encoding="utf-8")
    projects = extract_projects(text)
    by_num = {n: (title, body) for n, title, body in projects}

    for n in range(1, 26):
        title = fix_title(by_num[n][0])
        body = clean_body(by_num[n][1])
        m = META[n]
        extra = m.get("extra_steps_note", "")

        # Technologies heading
        tech_block = m.get("technologies") or m.get("tech", "")
        out = []
        out.append(f"# Project {n}: {title}\n")
        out.append("> **Playlist:** [AWS Cloud LABS](https://www.youtube.com/playlist?list=PL6rbQ5F5xbtUDapCqcNV0srF8Uu-8RtSt)\n")
        out.append("\n## Introduction\n\n")
        out.append(m["intro"].strip() + "\n")
        out.append("\n## Technologies and tools used\n\n")
        out.append(tech_block.strip() + "\n")
        if extra:
            out.append(extra)
        out.append("\n## Step-by-step lab walkthrough\n\n")
        if n == 1:
            out.append(
                "> **Console note (2025–2026):** IAM may show **Specify user details** and **Set permissions** as separate steps. "
                "Enable **Console access** when you want a password login, create or pick a **group**, attach **AdministratorAccess** to that group, then finish **Review and create**.\n\n"
            )
        if n == 3:
            out.append(
                "> **Direct link:** You can skip the search engine step and open the official [Installing or updating the latest AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) page, then choose **Windows**.\n\n"
            )
        if n == 10:
            out.append(
                "**Before Task 2 — Lambda execution role:** If `Lambda_role` does not exist, choose **Create a new role with basic Lambda permissions**, "
                "open the new role in **IAM**, and attach an inline policy (or customer policy) allowing `s3:GetObject` on `arn:aws:s3:::YOUR-SOURCE-BUCKET/*` "
                "and `s3:PutObject` on `arn:aws:s3:::YOUR-DEST-BUCKET/*`. The function copies objects between buckets; without S3 permissions the invoke will fail.\n\n"
            )
        if n == 9:
            out.append(
                "> **Amazon Linux 2023:** If your launch template uses AL2023, replace `yum` with `dnf` in user data (same commands otherwise). "
                "Amazon Linux 2 keeps `yum`.\n\n"
            )
        if n == 23:
            out.append(
                "> **Rule names change:** The video may list labels like *GeoLocationRestriction* or *QueryStringRestriction*. In **AWS WAF**, open **Add rules** → "
                "**Add managed rule groups** and search for **SQL**, **geo**, and **known bad inputs** (for example **Core rule set**, **SQL database**, **Anonymous IP list**). "
                "Pick groups that match your learning goals and set actions to **Block** or start with **Count**.\n\n"
            )
        out.append(body.strip() + "\n")
        out.append("\n## Conclusion\n\n")
        out.append(m["conclusion"].strip() + "\n")

        (root / f"{n}.md").write_text("\n".join(out), encoding="utf-8")
        print("Wrote", n, ".md")

if __name__ == "__main__":
    main()
