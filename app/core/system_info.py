"""
This file contains functions for getting system information in production for debugging.
"""

import platform
import re
import socket
import uuid
from datetime import datetime
import cpuinfo
import psutil
from app.core.log_config import get_logger

logger = get_logger(name=__name__)


class SystemInfo:
    """
    Contains functions for getting system information.
    """

    def get_size(self, byte, suffix="B"):
        """
        Scales bytes to its proper format.
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if byte < factor:
                return f"{byte:.2f}{unit}{suffix}"
            byte /= factor

    def system_information(self):
        """
        Contains the information of System.
        """
        try:
            logger.info("=" * 40 + "System Information" + "=" * 40)
            uname = platform.uname()
            logger.info(f"System: {uname.system}")
            logger.info(f"Node Name: {uname.node}")
            logger.info(f"Release: {uname.release}")
            logger.info(f"Version: {uname.version}")
            logger.info(f"Machine: {uname.machine}")
            logger.info(f"Processor: {uname.processor}")
            logger.info(f"Processor: {cpuinfo.get_cpu_info()['brand_raw']}")
            logger.info(f"Ip-Address: {socket.gethostbyname(socket.gethostname())}")
            logger.info(f"Mac-Address: {':'.join(re.findall('..', '%012x' % uuid.getnode()))}")

            # Boot Time
            logger.info("=" * 40 + "Boot Time" + "=" * 40)
            boot_time_timestamp = psutil.boot_time()
            bt = datetime.fromtimestamp(boot_time_timestamp)
            logger.info(f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}")

            # Print CPU information
            logger.info("=" * 40 + "CPU Info" + "=" * 40)

            # Number of cores
            try:
                logger.info("About to get physical cores")
                logger.info("Physical cores: %s", psutil.cpu_count(logical=False))
                logger.info("About to get total cores")
                logger.info("Total cores: %s", psutil.cpu_count(logical=True))
            except TypeError as e:
                logger.info("TypeError occurred")
                logger.error(str(e))
            except Exception as e:
                logger.info("Could not determine number of cores")
                logger.error(str(e))

            # CPU frequencies
            cpufreq = psutil.cpu_freq()
            if cpufreq:
                logger.info(f"Max Frequency: {cpufreq.max:.2f}Mhz")
                logger.info(f"Min Frequency: {cpufreq.min:.2f}Mhz")
                logger.info(f"Current Frequency: {cpufreq.current:.2f}Mhz")
            else:
                logger.info("Can't determine cpufreq")
            # CPU usage
            logger.info("CPU Usage Per Core:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
                logger.info(f"Core {i}: {percentage}%")
            logger.info(f"Total CPU Usage: {psutil.cpu_percent()}%")

            # Memory Information
            logger.info("=" * 40 + "Memory Information" + "=" * 40)
            # Get the memory details
            system_memory = psutil.virtual_memory()
            logger.info(f"Total: {self.get_size(system_memory.total)}")
            logger.info(f"Available: {self.get_size(system_memory.available)}")
            logger.info(f"Used: {self.get_size(system_memory.used)}")
            logger.info(f"Percentage: {system_memory.percent}%")
            # SWAP
            logger.info("=" * 20 + "SWAP" + "=" * 20)
            # Get the swap memory details (if exists)
            swap = psutil.swap_memory()
            logger.info(f"Total: {self.get_size(swap.total)}")
            logger.info(f"Free: {self.get_size(swap.free)}")
            logger.info(f"Used: {self.get_size(swap.used)}")
            logger.info(f"Percentage: {swap.percent}%")

            # Disk Information
            logger.info("=" * 40 + "Disk Information" + "=" * 40)
            logger.info("Partitions and Usage:")
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            for partition in partitions:
                logger.info(f"=== Device: {partition.device} ===")
                logger.info(f"  Mountpoint: {partition.mountpoint}")
                logger.info(f"  File system type: {partition.fstype}")
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                except PermissionError:
                    logger.error(f"Permission denied on disk partition: {partition.mountpoint}")
                    continue
                logger.info(f"  Total Size: {self.get_size(partition_usage.total)}")
                logger.info(f"  Used: {self.get_size(partition_usage.used)}")
                logger.info(f"  Free: {self.get_size(partition_usage.free)}")
                logger.info(f"  Percentage: {partition_usage.percent}%")

            # Get IO statistics since boot
            disk_io = psutil.disk_io_counters()
            logger.info(f"Total read: {self.get_size(disk_io.read_bytes)}")
            logger.info(f"Total write: {self.get_size(disk_io.write_bytes)}")

            # Network information
            logger.info("=" * 40 + "Network Information" + "=" * 40)

            # Get all network interfaces (virtual and physical)
            if_addrs = psutil.net_if_addrs()
            for interface_name, interface_addresses in if_addrs.items():
                for address in interface_addresses:
                    logger.info(f"=== Interface: {interface_name} ===")
                    if str(address.family) == "AddressFamily.AF_INET":
                        logger.info(f"  IP Address: {address.address}")
                        logger.info(f"  Netmask: {address.netmask}")
                        logger.info(f"  Broadcast IP: {address.broadcast}")
                    elif str(address.family) == "AddressFamily.AF_PACKET":
                        logger.info(f"  MAC Address: {address.address}")
                        logger.info(f"  Netmask: {address.netmask}")
                        logger.info(f"  Broadcast MAC: {address.broadcast}")

            # Get IO statistics since boot
            net_io = psutil.net_io_counters()
            logger.info(f"Total Bytes Sent: {self.get_size(net_io.bytes_sent)}")
            logger.info(f"Total Bytes Received: {self.get_size(net_io.bytes_recv)}")

        except Exception as e:
            logger.exception(f"An error occurred while getting system information: {str(e)}")
            