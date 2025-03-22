# Kisaan Mitra Backend

A comprehensive agricultural support system backend built with Django, designed to assist farmers in Haryana with various agricultural operations.

## Project Overview

Kisaan Mitra is a multi-faceted agricultural support system that integrates several key features:

- **Weather Monitoring**: Hyperlocal weather data and agricultural-specific analysis
- **Pest Detection**: AI-powered pest identification and management
- **AI Chatbot**: Intelligent assistant for farming queries
- **Crop Management**: Crop information and management tools
- **User Management**: Farmer profile management with regional customization

## Application Structure

The project consists of multiple Django apps:

- `weather/`: Weather monitoring and forecasting system
- `pest_detection/`: AI-based pest identification and management
- `chatbot/`: AI-powered farming assistant
- `crops/`: Crop management and information system
- `users/`: User profile and authentication management
- `ai_integration/`: AI services integration layer

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (create a .env file)

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Users
- User registration and authentication
- Farmer profile management
- Regional preferences

### Weather
- Hyperlocal weather monitoring
- Agricultural weather metrics
- Weather alerts and forecasts

### Pest Detection
- Pest identification
- Treatment recommendations
- Historical pest data

### Crops
- Crop information
- Growing guides
- Seasonal recommendations

### Chatbot
- Farming queries
- Real-time assistance
- Multi-language support

## Tech Stack

- **Framework**: Django
- **Database**: Default SQLite (configurable)
- **AI Integration**: Google's Gemini AI
- **API**: REST framework
- **Authentication**: JWT

## Development

- Follow PEP 8 style guidelines
- Write tests for new features
- Maintain documentation
- Use feature branches for development

## Testing

Run tests using:
```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

This project is proprietary and confidential. All rights reserved.
