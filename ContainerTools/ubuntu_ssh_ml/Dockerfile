FROM ubuntu:20.04

#
#    RUN statement is used to run commands when building the docker image.
#

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
	apt-get -y dist-upgrade && \ 
	apt-get install -y software-properties-common && \
	apt-get update && \
	apt-get -y install python3 python3-pip sudo libssl-dev libffi-dev && \
	apt-get install -y openssh-server wget vim net-tools  x11-apps

# check our python environment
RUN python3 --version
RUN pip3 --version


# Installing python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

 
RUN mkdir /var/run/sshd

# You must change the password 'opencesmii' to something else before you deploy on your system and uncomment the line
#RUN echo 'root:opencesmii' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

RUN mkdir -p /root/.ssh

#Copy public key to container and add that to authorized_keys
COPY id_rsa.pub /root/.ssh/id_rsa.pub


RUN cat root/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

ONBUILD ADD id_rsa.pub /root/.ssh/id_rsa.pub
ONBUILD RUN cat root/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
#Change permissions to meet ssh resitrictions
ONBUILD RUN chmod go-w ~/ && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys

# Create an user

RUN useradd -ms /bin/bash cesmii
# You must change the password 'opencesmii' to something else before you deploy on your system and uncomment the line

#RUN echo 'cesmii:opencesmii' | chpasswd
RUN usermod -aG sudo cesmii

USER cesmii

RUN mkdir -p /home/cesmii/.ssh
COPY id_rsa.pub /home/cesmii/.ssh/id_rsa.pub
RUN cat /home/cesmii/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
RUN chmod go-w ~/ && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys

COPY PythonGraphQLQuery.py /home/cesmii/PythonGraphQLQuery.py
COPY cesmii_credential_example.py /home/cesmii/cesmii_credential_example.py

USER root
RUN chmod 755 /home/cesmii/PythonGraphQLQuery.py
RUN chown cesmii:cesmii /home/cesmii/PythonGraphQLQuery.py

RUN chmod 755 /home/cesmii/cesmii_credential_example.py
RUN chown cesmii:cesmii /home/cesmii/cesmii_credential_example.py


ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

#ADD start.sh /

EXPOSE 22

# With ENTRYPOINT and CMD you can define what to run when you start a container using that image. 

CMD ["/usr/sbin/sshd", "-D"]

CMD service ssh start && while true; do sleep 30000; done

RUN service ssh start
#CMD ["service",  "ssh", "start"]

#CMD bash /start.sh
