read -p "Continue? (y/n) [THIS WILL DELETE ALL SAVEFILES] > " CONT
if [ "$CONT" = "y" ]; then
  cd savestates
  rm *.txt
  echo "Delete operation completed."
fi