# LLM Trick Game - FRED Challenge

## Overview
The **LLM Trick Game** is an interactive application where users attempt to trick an AI (FRED) into granting a "WIN" status. Players use credits for each attempt, and successful wins result in cash rewards.

## Features
- Interactive gameplay with an AI game master (FRED).
- Secure user authentication and session management.
- Credits-based system for gameplay.
- Integration with PayPal for credit purchases and cashouts.
- Backend logging and error handling for robust operations.

## Installation

### Prerequisites
- Python 3.12 or higher
- Flask and its dependencies
- PayPal REST SDK
- `.env` file with the following configurations:
  ```env
  FLASK_ENV=production
  FLASK_RUN_HOST=0.0.0.0
  FLASK_RUN_PORT=5000
  SECRET_KEY=your_secret_key

  # PayPal Credentials
  PAYPAL_CLIENT_ID=your_client_id
  PAYPAL_CLIENT_SECRET=your_client_secret

  # Game Configurations
  ATTEMPT_COST=1.00
  POT_AMOUNT=100.00
  HOUSE_CUT_PERCENT=10
  FEES_PERCENT=3.5

  # Logging
  LOG_PATH=./logs

  # LLM Configurations
  OLLAMA_MODEL=llama3.2


### Launching publicly SOON to play the game against Fred ####

