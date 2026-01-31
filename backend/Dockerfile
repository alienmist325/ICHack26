# Select base image
FROM python

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Set working directory
WORKDIR /home/app

# Copy repository
ADD . .

# Install repository and dependencies
RUN python -m pip install .

# Start Flask
CMD [ "flask", "run" ]
