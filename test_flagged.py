import drive, main
from state import load_state, save_state

state = load_state()
doc = next(d for d in drive.list_docs() if "Graduate Recruitment" in d["name"])
main.process_doc(doc, state)
save_state(state)