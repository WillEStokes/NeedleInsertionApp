# NeedleInsertionApp

## Description

Python app to control a needle insertion rig

## Needle Insertion Rig Control

This Python project enables control of a needle insertion rig equipped with the following components:

- Thorlabs Motorized Translation Stages: Three stages with IDs 27253326 (X-axis), 27253425 (Y-axis), and 27253356 (Z-axis).
- Kinesis® K-Cube™ Brushed DC Servo Motor Controllers: Three controllers for the motorized stages.
- mbed K64F Board: Main controller board.
- Mikroe Arduino Uno Click Shield: Interface board for Arduino Uno Click modules.
- Mikroe ADC 18 Click Board: Analog-to-digital converter board.

## Project Structure

├── main_app.py          # Main application file
├── lib/                 # Library folder
│   ├── __init__.py
│   └── stageController.py # Stage controller module
└── Display.py           # Display module

## Requirements
- Python 3.6+
- PyQt6
- pylablib

## Installation

Clone the repository:

git clone https://github.com/WillEStokes/NeedleInsertionApp.git

## Usage

Run main_app.py

## Functionality
- Control Interface: Provides controls for each axis (X, Y, Z) including homing, setting velocity, and moving by a specified distance.
- Sequence Management: Create, load, and save sequences of motions including movements and pauses.
- Logging: Logs sequence execution and status.
