# Journal v2.0 20250414.07:35
import os, json, uuid, tempfile, shutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from json import JSONDecodeError
import logger_journal
from logger_journal import log_error, log_debug

ENTRIES_FILE = "/bin/Python/Journal/entries.json"

class JournalStorage:
    def __init__(self, filename=ENTRIES_FILE):
        self.filename = filename

    def load_entries(self):
        if not os.path.exists(self.filename):
            log_debug(f"{self.filename} does not exist")
            return []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                entries = json.load(f)
                log_debug(f"Loaded {len(entries)} entries from {self.filename}.")
                return entries
        except JSONDecodeError as e:
            log_error(f"JSON error loading {self.filename}: {str(e)}")
            messagebox.showerror("Error", f"Data in {self.filename} corrupted")
            return []
        except Exception as e:
            log_error(f"Couldn't load {self.filename}: {str(e)}")
            messagebox.showerror("Error", f"Couldn't load {self.filename}: {str(e)}")
            return []

    def save_entries(self, entries):
        temp_filename = None
        try:
            dir_name = os.path.dirname(os.path.abspath(self.filename))
            with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
                temp_filename = tf.name
                json.dump(entries, tf, indent=4)
            shutil.move(temp_filename, self.filename)
            log_debug(f"Saved {len(entries)} entries to {self.filename}")
        except Exception as e:
            log_error(f"Error saving {self.filename}: {str(e)}")
            messagebox.showerror("Error Saving", str(e))
        finally:
            if temp_filename and os.path.exists(temp_filename):
                os.remove(temp_filename)

class JournalModel:
    def __init__(self, storage: JournalStorage):
        self.storage = storage
        self.entries = self.storage.load_entries()

    def add_entry(self, title: str, content: str):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry_number = len(self.entries) + 1
        new_entry = {"unique_id": str(uuid.uuid4()), "entry_number": entry_number, "title": title, "content": content, "date_time": date_time}
        self.entries.append(new_entry)
        self.storage.save_entries(self.entries)
        log_debug(f"Added Entry #{entry_number}: {title}")
        return new_entry

    def update_entry(self, index: int, title: str, content: str):
        if 0 <= index < len(self.entries):
            self.entries[index]["title"] = title
            self.entries[index]["content"] = content
            self.entries[index]["date_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.storage.save_entries(self.entries)
            log_debug(f"Updated Entry #{self.entries[index]['entry_number']}: {title}")
            return True
        log_error(f"Update failed: index {index} out of bounds")
        return False

    def delete_entry(self, index: int):
        if 0 <= index < len(self.entries):
            deleted_entry = self.entries.pop(index)
            for i, entry in enumerate(self.entries):
                entry["entry_number"] = i + 1
            self.storage.save_entries(self.entries)
            log_debug(f"Deleted Entry #{deleted_entry['entry_number']}: {deleted_entry['title']}")
            return True
        log_error(f"Deletion failed: index {index} out of bounds")
        return False

    def search_entries(self, keyword: str):
        keyword_lower = keyword.lower()
        results = []
        for idx, entry in enumerate(self.entries):
            if keyword_lower in entry["title"].lower() or keyword_lower in entry["content"].lower():
                results.append((idx, entry))
        log_debug(f"Search for '{keyword}' returned {len(results)} results")
        return results

class JournalController:
    def __init__(self, model: JournalModel):
        self.model = model

    def add_new_entry(self, title: str, content: str):
        if not title.strip():
            log_error("Attempted to add entry with empty title")
            raise ValueError("Title empty")
        new_entry = self.model.add_entry(title.strip(), content.strip())
        log_debug(f"JournalController added new entry: {new_entry['entry_number']} - {new_entry['title']}")
        return new_entry

    def edit_entry(self, index: int, title: str, content: str):
        if not title.strip():
            log_error("Attempted to edit entry with empty title")
            raise ValueError("Title empty.")
        if not self.model.update_entry(index, title.strip(), content.strip()):
            log_error(f"Failed to update entry at index {index}")
            raise IndexError("Couldn't update")
        log_debug(f"JournalController updated entry index {index}")

    def delete_entry(self, index: int):
        if not self.model.delete_entry(index):
            log_error(f"Failed to delete entry at index {index}")
            raise IndexError("Entry could not be deleted.")
        log_debug(f"JournalController deleted entry at index {index}")

    def get_all_entries(self):
        entries = self.model.entries
        log_debug(f"Retrieved all entries, total count: {len(entries)}")
        return entries

    def search(self, keyword: str):
        results = self.model.search_entries(keyword.strip())
        log_debug(f"JournalController search for '{keyword}' returned {len(results)} results")
        return results

class JournalView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.entry_listbox = None
        self.search_result_indexes = []
        self.bg_color = "black"
        self.fg_color = "white"
        self.widget_bg = "black"
        self.widget_fg = "white"

        self._create_main_interface()

    def _create_main_interface(self):
        log_debug("Painting the interface.")
        self.root.title("Journal")
        try:
            icon = tk.PhotoImage(file="journal_icon.png")
            self.root.iconphoto(False, icon)
        except Exception as e:
            log_error(f"Failed to load icon: {e}")
        
        self.root.geometry("480x665")
        self.root.configure(bg=self.bg_color)

        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(pady=10)

        self._create_label(top_frame, "Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.title_entry = tk.Entry(top_frame, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        self.title_entry.grid(row=1, column=0, padx=5, pady=5)
        self.title_entry.bind("<KeyRelease>", self._toggle_add_button)

        self._create_label(top_frame, "Content:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.content_text = tk.Text(top_frame, height=25, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        self.content_text.grid(row=3, column=0, padx=5, pady=5)

        bottom_frame = tk.Frame(self.root, bg=self.bg_color)
        bottom_frame.pack(pady=10)

        self.add_button = tk.Button(bottom_frame, text="Add", command=self._on_add_entry, state=tk.DISABLED, bg=self.widget_bg, fg=self.widget_fg)
        self.add_button.pack(side=tk.LEFT, padx=5)

        tk.Button(bottom_frame, text="List All", command=self._open_list_window, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Search", command=self._open_search_window, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Close", command=self.root.destroy, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)

    def _create_label(self, parent, text):
        return tk.Label(parent, text=text, bg=self.bg_color, fg=self.fg_color)

    def _toggle_add_button(self, event=None):
        title = self.title_entry.get().strip()
        if title:
            log_debug("Title exists, enabling Add button.")
            self.add_button.config(state=tk.NORMAL)
        else:
            log_debug("Title is empty, disabling Add button.")
            self.add_button.config(state=tk.DISABLED)

    def _on_add_entry(self):
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        log_debug("Attempting to add entry with title: '{}'".format(title))
        try:
            self.controller.add_new_entry(title, content)
            messagebox.showinfo("Success", "Entry added successfully.")
            log_debug("Entry added successfully.")
            self.title_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)
            self.title_entry.focus()
            self.add_button.config(state=tk.DISABLED)
        except ValueError as ve:
            log_error("Error adding entry: {}".format(ve))
            messagebox.showwarning("Missing Title", str(ve))

    def _open_list_window(self):
        entries = self.controller.get_all_entries()
        if not entries:
            log_debug("No entries found when opening list window.")
            messagebox.showinfo("No Entries", "There are no journal entries.")
            return

        log_debug("Opening list window with {} entries.".format(len(entries)))
        list_window = tk.Toplevel(self.root)
        list_window.title("Journal Entries")
        list_window.geometry("500x300")
        list_window.configure(bg=self.bg_color)

        list_frame = tk.Frame(list_window, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame, bg=self.bg_color)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.entry_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=self.widget_bg, fg=self.widget_fg)
        for entry in entries:
            display_text = f"Entry {entry['entry_number']}: {entry['title']} - {entry['date_time']}"
            self.entry_listbox.insert(tk.END, display_text)
        self.entry_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.entry_listbox.yview)

        button_frame = tk.Frame(list_window, bg=self.bg_color)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="View", command=self._view_selected_entry, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=lambda: self._open_edit_window(list_window), bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self._delete_selected_entry, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=list_window.destroy, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)

        def on_list_window_close():
            log_debug("List window closed. Resetting entry_listbox.")
            self.entry_listbox = None
            list_window.destroy()
        list_window.protocol("WM_DELETE_WINDOW", on_list_window_close)

    def _get_selected_index(self):
        if self.entry_listbox is None:
            log_error("Attempted selection access but listbox is not available.")
            messagebox.showwarning("List Not Available", "The entry list is not available.")
            return None
        selection = self.entry_listbox.curselection()
        if not selection:
            log_debug("No entry selected from listbox.")
            messagebox.showwarning("No Selection", "Please select an entry.")
            return None
        log_debug("Entry selected at index: {}".format(selection[0]))
        return selection[0]

    def _open_edit_window(self, parent_window, search_result_index=None, model_index=None):
        if model_index is None:
            idx = self._get_selected_index()
            if idx is None:
                return
            model_index = idx

        entries = self.controller.get_all_entries()
        if model_index < 0 or model_index >= len(entries):
            log_error("Invalid entry selected for editing.")
            messagebox.showerror("Error", "Invalid entry selected.")
            return

        selected_entry = entries[model_index]
        log_debug("Opening edit window for entry number: {}".format(selected_entry['entry_number']))
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Entry {selected_entry['entry_number']}")
        edit_window.geometry("480x665")
        edit_window.configure(bg=self.bg_color)
        edit_frame = tk.Frame(edit_window, bg=self.bg_color)
        edit_frame.pack(padx=10, pady=10)

        self._create_label(edit_frame, "Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        title_entry = tk.Entry(edit_frame, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        title_entry.grid(row=1, column=0, padx=5, pady=5)
        title_entry.insert(0, selected_entry["title"])

        self._create_label(edit_frame, "Content:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        content_text = tk.Text(edit_frame, height=22, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        content_text.grid(row=3, column=0, padx=5, pady=5)
        content_text.insert("1.0", selected_entry["content"])

        def update_entry():
            new_title = title_entry.get().strip()
            new_content = content_text.get("1.0", "end-1c").strip()
            log_debug("Attempting to update entry {} with new title: '{}'".format(selected_entry['entry_number'], new_title))
            try:
                self.controller.edit_entry(model_index, new_title, new_content)
                messagebox.showinfo("Updated", f"Entry {selected_entry['entry_number']} updated.")
                log_debug("Entry {} updated successfully.".format(selected_entry['entry_number']))
                edit_window.destroy()
                self._refresh_listbox()
            except ValueError as ve:
                log_error("ValueError during edit: {}".format(ve))
                messagebox.showwarning("Missing Title", str(ve))
            except IndexError as ie:
                log_error("IndexError during edit: {}".format(ie))
                messagebox.showerror("Error", str(ie))

        def cancel_edit():
            log_debug("Editing cancelled by user for entry {}.".format(selected_entry['entry_number']))
            if messagebox.askyesno("Cancel Edit", "Are you sure you want to cancel editing?"):
                edit_window.destroy()

        tk.Button(edit_frame, text="Save", command=update_entry, bg=self.widget_bg, fg=self.widget_fg).grid(row=4, column=0, pady=5, padx=5, sticky="w")
        tk.Button(edit_frame, text="Cancel", command=cancel_edit, bg=self.widget_bg, fg=self.widget_fg).grid(row=4, column=0, pady=5, padx=5, sticky="e")

    def _view_selected_entry(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        entries = self.controller.get_all_entries()
        if idx < 0 or idx >= len(entries):
            log_error("Invalid index selected for viewing.")
            messagebox.showerror("Error", "Invalid selection.")
            return
        entry = entries[idx]
        log_debug("Viewing entry number: {}".format(entry['entry_number']))
        self._open_view_window(entry)

    def _open_view_window(self, entry):
        log_debug("Opening view window for entry number: {}".format(entry['entry_number']))
        view_window = tk.Toplevel(self.root)
        view_window.title(f"View {entry['entry_number']}")
        view_window.geometry("480x665")
        view_window.configure(bg=self.bg_color)
        view_frame = tk.Frame(view_window, bg=self.bg_color)
        view_frame.pack(padx=10, pady=10)

        self._create_label(view_frame, "Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        title_entry = tk.Entry(view_frame, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        title_entry.grid(row=1, column=0, padx=5, pady=5)
        title_entry.insert(0, entry["title"])
        title_entry.config(state=tk.DISABLED)

        self._create_label(view_frame, "Content:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        content_text = tk.Text(view_frame, height=25, width=50, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        content_text.grid(row=3, column=0, padx=5, pady=5)
        content_text.insert("1.0", entry["content"])
        content_text.config(state=tk.DISABLED)

        tk.Button(view_frame, text="Close", command=view_window.destroy, bg=self.widget_bg, fg=self.widget_fg).grid(row=4, column=0, pady=5, sticky="e")

    def _delete_selected_entry(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        entries = self.controller.get_all_entries()
        if idx >= len(entries):
            log_error("Invalid index selected for deletion.")
            messagebox.showerror("Error", "Invalid selection.")
            return
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete Entry {entries[idx]['entry_number']}?")
        log_debug("User confirmed deletion: {}".format(confirm))
        if confirm:
            try:
                self.controller.delete_entry(idx)
                messagebox.showinfo("Deleted", "Entry deleted successfully.")
                log_debug("Entry at index {} deleted successfully.".format(idx))
                self._refresh_listbox()
            except IndexError as ie:
                log_error("IndexError during deletion: {}".format(ie))
                messagebox.showerror("Error", str(ie))

    def _refresh_listbox(self):
        if self.entry_listbox is not None:
            try:
                log_debug("Refreshing entry listbox.")
                self.entry_listbox.delete(0, tk.END)
                for entry in self.controller.get_all_entries():
                    display_text = f"Entry {entry['entry_number']}: {entry['title']} - {entry['date_time']}"
                    self.entry_listbox.insert(tk.END, display_text)
            except tk.TclError as te:
                log_error("TclError during refreshing listbox: {}".format(te))
                self.entry_listbox = None

    def _open_search_window(self):
        log_debug("Opening search window.")
        search_window = tk.Toplevel(self.root)
        search_window.title("Search")
        search_window.geometry("500x400")
        search_window.configure(bg=self.bg_color)
        frame = tk.Frame(search_window, bg=self.bg_color)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self._create_label(frame, "Keyword:").pack(anchor="w")
        keyword_entry = tk.Entry(frame, width=40, bg=self.widget_bg, fg=self.widget_fg, insertbackground=self.widget_fg)
        keyword_entry.pack(anchor="w", pady=5)

        result_listbox = tk.Listbox(frame, bg=self.widget_bg, fg=self.widget_fg)
        result_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = tk.Scrollbar(frame, command=result_listbox.yview, bg=self.bg_color)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_listbox.config(yscrollcommand=scrollbar.set)

        local_search_result_indexes = []

        def perform_search():
            keyword = keyword_entry.get().strip().lower()
            result_listbox.delete(0, tk.END)
            local_search_result_indexes.clear()
            if not keyword:
                log_debug("Empty keyword submitted for search.")
                messagebox.showwarning("No Keyword", "Please enter a keyword to search.")
                return
            results = self.controller.search(keyword)
            if not results:
                log_debug("No results found for keyword: '{}'".format(keyword))
                result_listbox.insert(tk.END, "No entries")
                return
            log_debug("Found {} search results for keyword: '{}'".format(len(results), keyword))
            for model_idx, entry in results:
                result_text = f"Entry {entry['entry_number']}: {entry['title']} - {entry['date_time']}"
                result_listbox.insert(tk.END, result_text)
                local_search_result_indexes.append(model_idx)

        def view_selected_search_entry():
            selection = result_listbox.curselection()
            if not selection:
                log_debug("No search result selected for viewing.")
                messagebox.showwarning("No Selection", "Please select a search result.")
                return
            sel_idx = selection[0]
            if sel_idx >= len(local_search_result_indexes):
                log_error("Selected search index out of range.")
                return
            model_index = local_search_result_indexes[sel_idx]
            entries = self.controller.get_all_entries()
            if model_index < 0 or model_index >= len(entries):
                log_error("Invalid entry selected from search results.")
                messagebox.showerror("Error", "Invalid entry selected.")
                return
            entry = entries[model_index]
            log_debug("Viewing search result entry number: {}".format(entry['entry_number']))
            self._open_view_window(entry)

        def edit_selected_search_entry():
            selection = result_listbox.curselection()
            if not selection:
                log_debug("No search result selected for editing.")
                messagebox.showwarning("No Selection", "Please select a search result.")
                return
            sel_idx = selection[0]
            if sel_idx >= len(local_search_result_indexes):
                log_error("Selected search index out of range for editing.")
                return
            model_index = local_search_result_indexes[sel_idx]
            log_debug("Editing search result entry at model index: {}".format(model_index))
            self._open_edit_window(search_window, model_index=model_index)
            perform_search()

        button_frame = tk.Frame(frame, bg=self.bg_color)
        button_frame.pack(pady=5, fill=tk.X)
        tk.Button(button_frame, text="Search", command=perform_search, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="View", command=view_selected_search_entry, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=edit_selected_search_entry, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=search_window.destroy, bg=self.widget_bg, fg=self.widget_fg).pack(side=tk.LEFT, padx=5)

def main():
    log_debug("Journal Up.")
    storage = JournalStorage()
    model = JournalModel(storage)
    controller = JournalController(model)
    root = tk.Tk()
    JournalView(root, controller)
    log_debug("Starting Tkinter loop.")
    root.mainloop()

if __name__ == "__main__":
    main()
