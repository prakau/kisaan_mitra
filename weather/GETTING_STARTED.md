# Getting Started with Weather Module

## Quick Setup

1. **Install Dependencies**
```bash
cd kisaan_mitra/weather
make install
```

2. **Configure Environment**
```bash
# Add to .env file
WEATHER_CACHE_TIMEOUT=300
WEATHER_MAX_FORECAST_DAYS=7
WEATHER_API_RATE_LIMIT=100
WEATHER_DATA_SOURCE=IMD
```

3. **Run Migrations**
```bash
make migrate
```

4. **Run Tests**
```bash
make test
```

## Development Workflow

1. **Start Development**
```bash
make dev-setup
```

2. **Before Committing Changes**
```bash
make check-all  # Runs formatting, linting, and tests
```

3. **Update Dependencies**
```bash
make update-deps
```

## API Usage Examples

1. **Get Current Weather**
```python
import requests

response = requests.get(
    'http://localhost:8000/api/weather/weather-data/current/',
    params={'location_id': 1},
    headers={'Authorization': 'Bearer <your-token>'}
)
```

2. **Get Weather Forecast**
```python
response = requests.get(
    'http://localhost:8000/api/weather/forecasts/weekly/',
    params={
        'location_id': 1,
        'crop_id': 1  # Optional: Get crop-specific insights
    },
    headers={'Authorization': 'Bearer <your-token>'}
)
```

3. **Get Active Alerts**
```python
response = requests.get(
    'http://localhost:8000/api/weather/alerts/active/',
    params={'location_id': 1},
    headers={'Authorization': 'Bearer <your-token>'}
)
```

## Data Models

1. **Location**
- name: Village/City name
- district: District name
- state: State name (defaults to Haryana)
- latitude: Geographical latitude
- longitude: Geographical longitude
- elevation: Elevation in meters

2. **WeatherData**
- location: ForeignKey to Location
- temperature: Temperature in Celsius
- humidity: Relative humidity percentage
- rainfall: Rainfall in mm
- wind_speed: Wind speed in km/h
- wind_direction: Wind direction in degrees
- soil_temperature: Soil temperature in Celsius
- soil_moisture: Soil moisture percentage
- solar_radiation: Solar radiation in W/m²

3. **WeatherForecast**
- Similar fields to WeatherData
- forecast_date: Date of forecast
- confidence_level: Forecast confidence percentage

## Code Organization

```
weather/
├── models.py          # Database models
├── repositories.py    # Data access layer
├── services.py       # Business logic
├── views.py          # API endpoints
├── serializers.py    # Data serialization
└── tests/            # Test suite
```

## Best Practices

1. **Code Style**
- Follow PEP 8
- Use type hints
- Write docstrings for all functions and classes

2. **Testing**
- Write tests for new features
- Maintain test coverage above 90%
- Use fixtures for common test data

3. **Git Workflow**
- Create feature branches
- Write descriptive commit messages
- Run `make check-all` before committing

4. **Error Handling**
- Use custom exceptions
- Provide meaningful error messages
- Log errors appropriately

## Common Issues

1. **Cache Issues**
```bash
# Clear cache if you see stale data
make clear-cache
```

2. **Migration Conflicts**
```bash
# Reset migrations
make clean
make makemigrations
make migrate
```

3. **Test Database Issues**
```bash
# Recreate test database
python manage.py reset_db --noinput
make migrate
```

## Performance Tips

1. Use `select_related()` and `prefetch_related()` for queries
2. Cache frequently accessed data
3. Use bulk operations for large datasets
4. Index frequently queried fields

## Monitoring

The module includes:
- Performance metrics
- Error tracking
- Usage statistics
- API response times

Access monitoring at: `/admin/weather/metrics/`

## Support

For issues and questions:
1. Check the documentation
2. Review test cases for examples
3. Contact the development team

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests
5. Submit pull request

Remember to keep the code clean, documented, and well-tested!