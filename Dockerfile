FROM mrismanaziz/man-userbot:buster

RUN git clone -b alpha https://github.com/mrismanaziz/Man-Userbot /home/manuserbot/ \
    && chmod 777 /home/manuserbot \
    && mkdir /home/manuserbot/bin/

COPY ./sample_config.env ./config.env* /home/manuserbot/

WORKDIR /home/manuserbot/

RUN pip3 install --use-deprecated=legacy-resolver -r requirements.txt

CMD ["python3", "-m", "userbot"]
