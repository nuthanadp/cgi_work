# APS (Automatic Payment System) - POC with AI-Driven Rule Suggestions

## Overview
This POC demonstrates an Automatic Payment System with intelligent repair functionality and AI-powered rule suggestion engine.

## System Components

### Core Features
- **Payment Processing**: Processes payments with account validation
- **Automatic Repair**: Rule-based account repair system
- **Manual Repair**: Interface for manual account corrections
- **Audit Logging**: Comprehensive logging of manual repairs
- **AI Analysis**: Pattern recognition and auto-repair rule suggestions

### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Payment        │    │  Account        │    │  Auto Repair    │
│  Processor      │───▶│  Validator      │───▶│  Engine         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Manual Repair  │    │  Audit Logger   │
                       │  Interface      │───▶│                 │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                              ┌─────────────────┐    ┌─────────────────┐
                              │  AI Pattern     │◀───│  Audit Data     │
                              │  Analyzer       │    │  Storage        │
                              └─────────────────┘    └─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Rule           │
                              │  Suggester      │
                              └─────────────────┘
```

## Key Features

### Audit Logging Format
- **DR_ACCOUNT_MANUAL_REPAIR**: Debitor account manual repairs
- **CR_ACCOUNT_MANUAL_REPAIR**: Creditor account manual repairs

### AI Capabilities
- Pattern recognition in manual repairs
- Feasibility analysis for automation
- Intelligent rule suggestions
- Learning from repair history

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## Directory Structure
```
src/
├── core/           # Core business logic
├── models/         # Data models
├── logging/        # Audit logging system
├── ai/            # AI analysis components
├── storage/       # Data persistence
└── api/           # Manual repair interface
```