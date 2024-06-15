# NeedleInsertionApp

PyQt6 app to control a bespoke needle insertion test system.

## Needle Insertion Rig Control

This Python project enables control of a bespoke needle insertion test system, equipped with the following components:

- Thorlabs Motorised Translation Stages: Three stages (X-axis, Y-axis and Z-axis).
- Kinesis® K-Cube™ Brushed DC Servo Motor Controllers: Three controllers for the motorised stages.
- Mbed FRDM K64F board: Data acquisition board.
- Mikroe Arduino Uno Click Shield: Interface board for mbed K64F with Mikroe Click modules.
- Mikroe ADC 18 Click Board: Analog-to-digital converter board for multi-channel differential measurements.

## Project Structure

```
├── main_app.py               # Main application file
├── lib/                      # Library folder
│   ├── K64F.py               # K64F interface module and data logging
│   └── stageController.py    # Linear stage interface module
└── src/                      # Source folder
    ├── needleInsertionApp.py # User interface for configuring stage control and file IO
    └── Display.py            # Data display module
```

## Requirements
- Python 3.6+
- PyQt6
- pylablib

## Installation

Clone the repository:

```
git clone https://github.com/WillEStokes/NeedleInsertionApp.git
```

## Usage

Run main_app.py

## Functionality
- Control Interface: Provides controls for each axis (X, Y, Z) including homing, setting velocity, and moving by a specified distance.
- Sequence Management: Create, load, and save sequences of motions including movements and pauses.
- Logging: Logs FT sensor measurements and encoder positions.
