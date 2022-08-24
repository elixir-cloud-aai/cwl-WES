CODE=$(curl --write-out '%{http_code}' --output /dev/null --silent localhost:8080/ga4gh/wes/v1/runs)
if [ $CODE != "200" ]
then
  exit 1;
fi