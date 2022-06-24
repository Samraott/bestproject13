if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/NoobEditorCodes/XtremeCoreUpdated.git /XtremeCoreUpdated
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /XtremeCoreUpdated
fi
cd /XtremeCoreUpdated
pip3 install -U -r requirements.txt
echo "Starting Bot 🦋🦋"
python3 bot.py
