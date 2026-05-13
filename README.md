\# Autonomous Line Following Warehouse Robot



Autonomous line-following warehouse robot built using a Raspberry Pi 4B, QTR-MD-07RC IR sensor array, ultrasonic obstacle detection, and differential drive motor control. The robot follows predefined paths using calibrated infrared sensors and safely stops when obstacles are detected in front of it.



> Full technical documentation available in: `Robot\_Line\_Follower\_Documentation.pdf` :contentReference\[oaicite:0]{index=0}



\---



\## Project Overview



This project demonstrates an autonomous warehouse-style mobile robot capable of:



\- Following a predefined black or white tape path

\- Detecting obstacles using ultrasonic sensing

\- Dynamically adjusting wheel speeds using PWM motor control

\- Calibrating IR sensors automatically for different surfaces

\- Running fully autonomously on battery power



The system combines optoelectronics, embedded software, GPIO interfacing, and real-time sensor processing using Python on Raspberry Pi.



\---



\# Robot Demonstration



\## Robot Hardware



<p align="center">

&#x20; <img src="images/Photo\_of\_Robot.png" width="600">

</p>



\---



\## Robot Following the Track



<p align="center">

&#x20; <img src="images/Robot on track.png" width="700">

</p>



\---



\# Main Features



\- \*\*Autonomous Line Following\*\*

&#x20; - Uses QTR-MD-07RC infrared sensor array

&#x20; - Real-time tape position detection

&#x20; - Weighted sensor position calculation



\- \*\*Obstacle Detection\*\*

&#x20; - HC-SR04 ultrasonic sensor

&#x20; - Stops robot approximately 20 cm before collision



\- \*\*IR Sensor Calibration System\*\*

&#x20; - Automatic threshold calculation

&#x20; - Threshold validation and safety checks

&#x20; - Calibration data persistence using text files



\- \*\*Differential Drive Motor Control\*\*

&#x20; - PWM-based speed control

&#x20; - Dynamic steering correction

&#x20; - Independent wheel adjustment



\- \*\*Multithreaded Sensor Monitoring\*\*

&#x20; - Concurrent obstacle monitoring

&#x20; - Non-blocking robot movement



\---



\# Hardware Components



| Component | Purpose |

|---|---|

| Raspberry Pi 4B | Main controller |

| QTR-MD-07RC IR Array | Line detection |

| HC-SR04 Ultrasonic Sensor | Obstacle detection |

| L298N Motor Driver | DC motor control |

| 2x DC Motors | Differential drive |

| Li-Ion Battery Packs | Portable power system |

| LM2596 Voltage Regulators | Voltage regulation |



\---



\# System Architecture



\## Raspberry Pi GPIO Connections



<p align="center">

&#x20; <img src="images/Raspberry\_Pi\_pin\_connections.png" width="800">

</p>



\---



\## Electrical Schematic



<p align="center">

&#x20; <img src="images/robot\_schematic.png" width="1000">

</p>



\---



\# Software Architecture



The project software is divided into two main Python files:



```text

Robot\_main.py

│

├── Motor Control

├── Ultrasonic Monitoring

├── Main Robot Loop

├── IR Position Processing

└── Steering Logic



IRCollaboration.py

│

├── IR Calibration

├── Sensor Sampling

├── Threshold Generation

├── Threshold Validation

└── Threshold File Management

