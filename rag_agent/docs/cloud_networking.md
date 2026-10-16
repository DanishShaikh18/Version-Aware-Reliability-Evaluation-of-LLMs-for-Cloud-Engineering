# Google Cloud Networking: VPC, Subnets, Firewall Rules, and Connectivity

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://cloud.google.com/vpc/docs/overview
  - https://cloud.google.com/vpc/docs/firewalls
  - https://cloud.google.com/nat/docs/overview
  - https://cloud.google.com/vpc/docs/private-google-access
  - https://cloud.google.com/dns/docs/overview
  - https://cloud.google.com/load-balancing/docs/load-balancing-overview
- **gcloud CLI version verified:** Google Cloud SDK 576.0.0

---

## What Is a VPC Network?

A **Virtual Private Cloud (VPC)** network in Google Cloud is a global, software-defined network that provides:
- Connectivity between Compute Engine VMs, GKE nodes, Cloud Run services, and other resources.
- Isolation and security via firewall rules.
- Control over IP address ranges (subnets), routing, DNS, and egress.

**Google Cloud VPC networks are global** — a single VPC can have subnets in multiple regions. This is different from AWS VPCs, which are regional.

---

## Subnet Modes

| Mode | Description |
|---|---|
| **Auto mode** | Google automatically creates one subnet per region with predefined ranges. Quick to set up; not recommended for production. |
| **Custom mode** | You define subnets, regions, and CIDR ranges explicitly. Required for production workloads. |

```bash
# Create a custom-mode VPC (recommended for production)
gcloud compute networks create my-vpc \
    --subnet-mode=custom

# Create an auto-mode VPC (for quick experimentation)
gcloud compute networks create my-vpc-auto \
    --subnet-mode=auto

# List VPC networks
gcloud compute networks list
```

---

## Subnets

Subnets are **regional** resources within a VPC. Each subnet has a primary CIDR range.

```bash
# Create a subnet in a specific region
gcloud compute networks subnets create my-subnet \
    --network=my-vpc \
    --region=us-central1 \
    --range=10.10.1.0/24

# List subnets
gcloud compute networks subnets list --network=my-vpc

# Describe a subnet (shows CIDR, region, secondary ranges, etc.)
gcloud compute networks subnets describe my-subnet --region=us-central1
```

### CIDR Examples
| CIDR | First IP | Last IP | Hosts |
|---|---|---|---|
| `10.0.0.0/24` | `10.0.0.0` | `10.0.0.255` | 254 usable |
| `10.10.1.0/24` | `10.10.1.0` | `10.10.1.255` | 254 usable |
| `192.168.0.0/16` | `192.168.0.0` | `192.168.255.255` | 65,534 usable |
| `10.0.0.0/8` | `10.0.0.0` | `10.255.255.255` | ~16M usable |

**Common mistake:** Overlapping CIDR ranges between subnets in the same VPC or between VPCs that are peered — this causes routing conflicts.

---

## Firewall Rules

VPC firewall rules are **stateful** (return traffic is automatically allowed) and applied at the **network level** (not the subnet level). Rules target specific VMs using network tags or service accounts.

```bash
# Allow SSH (port 22) from anywhere — USE CAREFULLY, restrict source ranges in production
gcloud compute firewall-rules create allow-ssh \
    --network=my-vpc \
    --direction=INGRESS \
    --priority=1000 \
    --action=ALLOW \
    --rules=tcp:22 \
    --source-ranges=0.0.0.0/0

# Allow HTTP and HTTPS for web servers tagged "web-server"
gcloud compute firewall-rules create allow-http-https \
    --network=my-vpc \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=web-server

# Allow internal traffic within the subnet
gcloud compute firewall-rules create allow-internal \
    --network=my-vpc \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:0-65535,udp:0-65535,icmp \
    --source-ranges=10.10.1.0/24

# List all firewall rules for a VPC
gcloud compute firewall-rules list --filter="network:my-vpc"

# Delete a firewall rule
gcloud compute firewall-rules delete allow-ssh
```

### Firewall Priority
- Lower number = higher priority.
- Default: `1000`.
- Rules with `DENY` and lower priority number override `ALLOW` rules with higher numbers.

---

## IP Addresses

### Internal IP Addresses
- Every VM gets an internal IP from its subnet's CIDR range.
- Used for private communication within the VPC.

### External IP Addresses
- Optional; added to VMs that need public internet access.
- Can be **ephemeral** (changes on restart) or **static** (reserved).

```bash
# Reserve a static external IP
gcloud compute addresses create my-static-ip \
    --region=us-central1

# List reserved IP addresses
gcloud compute addresses list
```

---

## Routes

Routes define how traffic leaves a VPC network.

```bash
# List routes in a VPC
gcloud compute routes list --filter="network:my-vpc"
```

Default routes:
- `0.0.0.0/0` via default internet gateway — handles internet-bound traffic for VMs with external IPs.
- Subnet routes — automatically created for each subnet.

---

## Private Google Access

Allows VMs **without** external IP addresses to reach Google APIs (Cloud Storage, BigQuery, Vertex AI, etc.) via Google's internal network.

```bash
# Enable Private Google Access on a subnet
gcloud compute networks subnets update my-subnet \
    --region=us-central1 \
    --enable-private-ip-google-access

# Verify
gcloud compute networks subnets describe my-subnet \
    --region=us-central1 \
    --format="value(privateIpGoogleAccess)"
```

**When to use:** Any VM or workload that must reach Google APIs without a public IP (security best practice).

---

## Cloud NAT

Cloud NAT allows VMs without external IP addresses to initiate **outbound** internet connections (e.g., to download packages or call external APIs) without exposing them to inbound connections.

Cloud NAT requires a **Cloud Router**.

```bash
# Step 1: Create a Cloud Router
gcloud compute routers create my-router \
    --network=my-vpc \
    --region=us-central1

# Step 2: Configure Cloud NAT on the router
gcloud compute routers nats create my-nat \
    --router=my-router \
    --region=us-central1 \
    --auto-allocate-nat-external-ips \
    --nat-all-subnet-ip-ranges-rule

# Verify NAT configuration
gcloud compute routers nats describe my-nat \
    --router=my-router \
    --region=us-central1
```

**Difference between Private Google Access and Cloud NAT:**
- **Private Google Access:** Access to Google APIs only; no general internet.
- **Cloud NAT:** General outbound internet access for VMs without external IPs.

---

## DNS in Google Cloud

Google Cloud provides **Cloud DNS**, a managed, authoritative DNS service.

```bash
# Create a managed DNS zone
gcloud dns managed-zones create my-zone \
    --dns-name="example.com." \
    --description="My DNS zone"

# Add an A record
gcloud dns record-sets create www.example.com. \
    --zone=my-zone \
    --type=A \
    --ttl=300 \
    --rrdatas="34.120.0.1"
```

---

## Load Balancing

Google Cloud offers several load balancer types:

| Type | Use Case |
|---|---|
| **Application Load Balancer (HTTP/HTTPS)** | HTTP/HTTPS traffic; URL-based routing; global or regional. |
| **Network Load Balancer (TCP/UDP)** | High-performance layer 4 load balancing; regional. |
| **Internal HTTP(S) LB** | HTTP/HTTPS traffic between internal VPC resources. |
| **Internal TCP/UDP LB** | TCP/UDP traffic between internal VPC resources. |

Cloud Run services use Google's global HTTP infrastructure automatically and do not require manually configuring a load balancer for basic use.

---

## Networking Diagnostics

```bash
# Test connectivity to a destination (from a Compute Engine VM)
# (Run from inside the VM)
ping 8.8.8.8
curl -I https://storage.googleapis.com

# Trace the route to a destination
traceroute 8.8.8.8   # Linux/macOS
tracert 8.8.8.8      # Windows

# Check firewall rules affecting a VM
gcloud compute firewall-rules list \
    --filter="network:my-vpc"

# Check routes
gcloud compute routes list --filter="network:my-vpc"

# Connectivity Tests (GCP tool — tests connectivity without running actual traffic)
# Requires roles/networkmanagement.admin
gcloud network-management connectivity-tests create my-test \
    --source-ip=10.10.1.5 \
    --destination-ip=10.10.2.10 \
    --protocol=TCP \
    --destination-port=80
```

---

## Security Guidance

1. Use **custom subnet mode** and define subnets only for regions you need.
2. Avoid `0.0.0.0/0` as a source range in firewall rules wherever possible; restrict to known CIDR ranges.
3. Use **network tags** or **service account-based** firewall rules rather than IP-based rules for application-level control.
4. Enable **VPC Flow Logs** to monitor traffic for security investigations.
5. Use **Private Google Access** to avoid giving VMs external IPs.
6. Use **Cloud NAT** (not external IPs) for VMs that need outbound internet access.
7. Disable the **default network** in production organisations; create custom VPCs with defined firewall rules.

---

## GCP Networking vs General Networking Concepts

| Concept | Universal | GCP-Specific Note |
|---|---|---|
| CIDR notation | Yes | Same as standard networking |
| Subnets | Yes | GCP subnets are regional; the VPC is global |
| Firewall rules | Yes | GCP rules are stateful; applied at network level, not VM level |
| NAT | Yes | Cloud NAT is a managed service; no NAT instance required |
| DNS | Yes | Cloud DNS is managed; internal DNS is auto-created per project |
| Load balancers | Yes | GCP LBs are distributed and highly available by default |

---

## Common Errors and Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| VM cannot reach the internet | No external IP or no Cloud NAT | Add external IP or configure Cloud NAT |
| VM cannot reach Google APIs | Private Google Access not enabled | Enable Private Google Access on the subnet |
| SSH blocked | No firewall rule for port 22 | Create an ingress rule for `tcp:22` |
| Overlapping CIDR | Subnet ranges conflict | Plan IP address ranges before creating subnets |
| Peering cannot be established | Overlapping CIDRs in peered VPCs | Redesign CIDR allocations |

---

## Official References
- VPC overview: https://cloud.google.com/vpc/docs/overview
- Firewall rules: https://cloud.google.com/vpc/docs/firewalls
- Cloud NAT: https://cloud.google.com/nat/docs/overview
- Private Google Access: https://cloud.google.com/vpc/docs/private-google-access
- Cloud DNS: https://cloud.google.com/dns/docs/overview
- Load balancing overview: https://cloud.google.com/load-balancing/docs/load-balancing-overview
