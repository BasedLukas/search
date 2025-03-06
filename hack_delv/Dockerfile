FROM public.ecr.aws/lambda/python:3.12

# Set Lambda task root
ENV LAMBDA_TASK_ROOT=/var/task

# Copy project files first
COPY . ${LAMBDA_TASK_ROOT}/

# Set up API key
ARG BRAVE_API_KEY
ENV BRAVE_API_KEY=${BRAVE_API_KEY}

# Install dependencies
RUN pip install -e .

# Set the CMD to your handler
CMD [ "src.lambda_function.lambda_handler" ]

