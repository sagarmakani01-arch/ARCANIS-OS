# Arcanis OS — User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Commands](#basic-commands)
3. [File Operations](#file-operations)
4. [Process Management](#process-management)
5. [Networking](#networking)
6. [Security](#security)
7. [Virtualization](#virtualization)
8. [Containers](#containers)
9. [GUI Desktop](#gui-desktop)
10. [Development](#development)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Download the Arcanis OS ISO image
2. Create a bootable USB drive
3. Boot from USB
4. Follow the installation wizard

### First Boot

After installation, Arcanis OS will boot to the login screen:
```
Arcanis OS v2.0.0
Login: user
Password: user
```

## Basic Commands

### Navigation

```bash
# List files
ls

# Change directory
cd /home/user

# Print working directory
pwd

# Show directory tree
tree /
```

### File Operations

```bash
# Create file
touch myfile.txt

# Edit file
vi myfile.txt
nano myfile.txt

# View file
cat myfile.txt

# Copy file
cp source.txt dest.txt

# Move/rename file
mv old.txt new.txt

# Remove file
rm myfile.txt
```

### Text Processing

```bash
# Search in file
grep pattern file.txt

# Count lines/words
wc file.txt

# Show first/last lines
head file.txt
tail file.txt

# Process text
awk '{print $1}' file.txt
```

## Process Management

### Viewing Processes

```bash
# List processes
ps

# Interactive process monitor
top
htop

# Show process tree
pstree
```

### Controlling Processes

```bash
# Run in background
sleep 100 &

# List background jobs
jobs

# Bring to foreground
fg %1

# Send to background
bg %1

# Kill process
kill <pid>
kill -9 <pid>
```

### Process Information

```bash
# Show process details
ps aux

# Show open files
lsof <pid>

# Show process memory
pmap <pid>
```

## Networking

### Network Configuration

```bash
# Show interfaces
ifconfig

# Configure interface
ifconfig eth0 192.168.1.100 netmask 255.255.255.0

# Show routing table
route

# Add route
route add -net 10.0.0.0/8 gw 192.168.1.1
```

### Network Diagnostics

```bash
# Test connectivity
ping google.com

# DNS lookup
nslookup example.com
dig example.com

# Trace route
traceroute google.com

# Show connections
netstat -tulpn
```

### Network Services

```bash
# Start SSH server
systemctl start sshd

# Start web server
systemctl start nginx

# Start DHCP client
dhclient eth0
```

### Firewall

```bash
# List rules
iptables -L

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Block IP
iptables -A INPUT -s 10.0.0.5 -j DROP

# Flush rules
iptables -F
```

### VPN

```bash
# Create VPN tunnel
vpn create office --type wireguard

# Connect to VPN
vpn connect office --remote vpn.company.com:51820

# Show VPN status
vpn status office

# Disconnect
vpn disconnect office
```

## Security

### User Management

```bash
# List users
user list

# Add user
user add john

# Delete user
user delete john

# Change password
passwd john
```

### File Permissions

```bash
# Change permissions
chmod 755 script.sh

# Change owner
chown user:group file.txt

# View permissions
ls -la file.txt
```

### Encryption

```bash
# Encrypt file
encrypt secret.txt mypassword

# Decrypt file
decrypt secret.txt mypassword

# Generate password
passwd --generate
```

### Audit

```bash
# View security log
cat /var/log/audit.log

# Check failed logins
lastb

# Show login history
last
```

## Virtualization

### Managing VMs

```bash
# Create VM
vm create myvm --memory 2G --disk 20G

# Start VM
vm start myvm

# Stop VM
vm stop myvm

# List VMs
vm list

# Connect to VM console
vm console myvm
```

### VM Operations

```bash
# Take snapshot
vm snapshot myvm --name snap1

# Restore snapshot
vm restore myvm snap1

# Clone VM
vm clone myvm myvm-copy

# Delete VM
vm destroy myvm
```

## Containers

### Container Operations

```bash
# Run container
docker run -d --name web nginx

# List containers
docker ps -a

# Stop container
docker stop web

# Remove container
docker rm web

# Execute command
docker exec web /bin/sh
```

### Image Management

```bash
# Pull image
docker pull nginx:latest

# List images
docker images

# Build image
docker build -t myapp .

# Remove image
docker rmi nginx
```

### Container Networking

```bash
# List networks
docker network ls

# Create network
docker network create mynet

# Run container on network
docker run --network mynet --name web nginx

# Inspect network
docker network inspect mynet
```

### Container Resources

```bash
# Set CPU limit
docker run --cpus="1.5" nginx

# Set memory limit
docker run --memory="512m" nginx

# View stats
docker stats
```

## GUI Desktop

### Window Management

- **Super+Click**: Move window
- **Super+Q**: Close window
- **Super+M**: Maximize window
- **Super+N**: Minimize window
- **Super+Tab**: Switch windows

### Applications

- **File Manager**: Graphical file browser
- **Terminal**: Command line interface
- **Text Editor**: Code and text editing
- **Web Browser**: Internet browsing
- **System Monitor**: Resource monitoring

### Settings

- **Display**: Resolution and scaling
- **Network**: Connection settings
- **Sound**: Audio configuration
- **Appearance**: Theme and colors

## Development

### Build Tools

```bash
# Compile C program
gcc -o program program.c

# Assemble
nasm -f elf32 program.s

# Link
ld -o program program.o

# Build project
make
```

### Debugging

```bash
# Debug program
gdb ./program

# Trace system calls
strace ./program

# Trace library calls
ltrace ./program
```

### Package Management

```bash
# Search packages
pkg search vim

# Install package
pkg install vim

# Remove package
pkg remove vim

# Update packages
pkg update
```

## Shell Scripting

### Variables

```bash
# Set variable
name="Arcanis"

# Use variable
echo $name

# Command substitution
today=$(date)
```

### Conditionals

```bash
# If statement
if [ -f file.txt ]; then
    echo "File exists"
fi

# If-else
if [ "$name" = "Arcanis" ]; then
    echo "Hello, Arcanis!"
else
    echo "Unknown"
fi
```

### Loops

```bash
# For loop
for i in 1 2 3; do
    echo $i
done

# While loop
count=0
while [ $count -lt 5 ]; do
    echo $count
    count=$((count + 1))
done
```

### Functions

```bash
# Define function
greet() {
    echo "Hello, $1!"
}

# Call function
greet "World"
```

## Troubleshooting

### Boot Issues

1. Check BIOS settings for boot order
2. Verify ISO integrity
3. Try recovery mode

### Network Issues

```bash
# Check interface status
ifconfig eth0

# Test connectivity
ping 8.8.8.8

# Check DNS
cat /etc/resolv.conf

# Restart network
systemctl restart network
```

### Performance Issues

```bash
# Check CPU usage
top

# Check memory
free -h

# Check disk
df -h

# Check I/O
iostat
```

### Logging

```bash
# System log
dmesg

# Application log
journalctl

# Security log
cat /var/log/secure
```

## Support

- **Documentation**: `/usr/share/doc/arcanis/`
- **Man Pages**: `man <command>`
- **Community Forum**: https://forum.arcanis.io
- **Bug Reports**: https://github.com/arcanis-os/issues
