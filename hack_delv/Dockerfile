FROM public.ecr.aws/lambda/python:3.12

# Set Lambda task root
ENV LAMBDA_TASK_ROOT=/var/task

# Copy project files first
COPY . ${LAMBDA_TASK_ROOT}/

# Configure API keys in Lambda runtime settings; none are embedded here.

# Install dependencies
RUN pip install -e .

# Set the CMD to your handler
CMD [ "src.lambda_function.lambda_handler" ]

