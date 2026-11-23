# AWS Emulator (https://github.com/aws/aws-emulator): AWS no publica una imagen; esta es la receta oficial de su guía de Docker.
# AWS emulado: plano de control, sin tráfico. Solo para el laboratorio; nunca para producción.
FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal
ADD https://downloads.aws.com/aws-emulator/packages/aws-emulator/LTS/latest/aws-emulator-x86_64.rpm /tmp/aws-emulator.rpm
RUN rpm -i /tmp/aws-emulator.rpm && rm /tmp/aws-emulator.rpm && mkdir -p /home/emulator && chown 1000 /home/emulator
USER 1000
ENV HOME=/home/emulator EMULATOR_BIND_ADDRESS=0.0.0.0 EMULATOR_TELEMETRY=off
ENTRYPOINT ["aws-emulator"]
