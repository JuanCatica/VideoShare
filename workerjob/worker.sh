# Get the worker script directory
WORKER_SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
cd $WORKER_SCRIPT_DIR
source vsvenv/bin/activate

# CHhecks if there is a worker.py running
# pgrep: Looks through the currently running processes and lists the process IDs which match the selection criteria to stdout.
if ! pgrep -f 'worker.py'
then
    nohup python ./worker.py > ./logs/super.log &
else
	echo "Overlap:" `date` >> ./logs/overlaps.log
fi

deactivate
#* * * * * bash /home/admin/videoshare/worker.sh