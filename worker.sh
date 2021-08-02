# Get the worker script directory
WORKER_SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
cd $WORKER_SCRIPT_DIR
source vsvenv/bin/activate

# CHhecks if there is a batch_transform_video.py running
# pgrep: Looks through the currently running processes and lists the process IDs which match the selection criteria to stdout.
if ! pgrep -f 'batch_transform_video.py'
then
    nohup python ./workerjob/batch_transform_video.py > ./workerjob/logs/super.log &
else
	echo "Overlap:" `date` >> ./workerjob/logs/overlaps.log
fi

deactivate

#* * * * * bash /home/admin/videoshare/worker.sh