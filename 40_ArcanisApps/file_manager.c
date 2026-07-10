/**
 * file_manager.c — File Manager Implementation
 *
 * Directory listing, navigation, and file operations.
 */
#include <arcanis/file_manager.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

int fm_init(file_manager_t* fm, wm_state_t* wm, gui_state_t* gui) {
    if (!fm || !wm || !gui) return -1;
    memset(fm, 0, sizeof(file_manager_t));
    fm->wm = wm;
    fm->gui = gui;
    string_copy(fm->cwd, "/", FM_MAX_PATH);

    /* Create window */
    fm->window_id = wm_create_window(wm, "File Manager", 100, 50, 700, 500, WIN_TYPE_NORMAL);
    wm_set_colors(wm, fm->window_id, 0x1E1E2E, 0xCDD6F4, 0x45475A);

    /* Create toolbar */
    fm->toolbar_id = gui_create_panel(gui, 100, 74, 700, 36);

    /* Create buttons */
    fm->up_btn_id = gui_create_button(gui, "..", 108, 78, 40, 28);
    fm->home_btn_id = gui_create_button(gui, "Home", 152, 78, 60, 28);
    fm->refresh_btn_id = gui_create_button(gui, "R", 216, 78, 28, 28);
    fm->new_dir_btn_id = gui_create_button(gui, "+Dir", 248, 78, 50, 28);
    fm->delete_btn_id = gui_create_button(gui, "Del", 302, 78, 40, 28);
    fm->rename_btn_id = gui_create_button(gui, "Ren", 346, 78, 40, 28);
    fm->copy_btn_id = gui_create_button(gui, "Cp", 390, 78, 36, 28);
    fm->paste_btn_id = gui_create_button(gui, "Pt", 430, 78, 36, 28);

    /* Path label */
    fm->path_label_id = gui_create_label(gui, "/", 470, 82);

    /* File list */
    fm->file_list_id = gui_create_list(gui, 100, 114, 700, 380);

    /* Status label */
    fm->status_label_id = gui_create_label(gui, "Ready", 100, 524);

    /* Open root */
    fm_open_dir(fm, "/");

    return 0;
}

int fm_open_dir(file_manager_t* fm, const char* path) {
    if (!fm || !path) return -1;

    string_copy(fm->cwd, path, FM_MAX_PATH);
    fm->current_dir.num_entries = 0;
    fm->current_dir.selected_idx = 0;
    fm->current_dir.scroll_offset = 0;

    /* Populate with default entries */
    if (string_compare(path, "/") == 0) {
        const char* root_dirs[] = {
            "dev", "etc", "home", "lib", "proc", "tmp", "usr", "var", "bin", "root", NULL
        };
        for (int i = 0; root_dirs[i]; i++) {
            fm_entry_t* e = &fm->current_dir.entries[fm->current_dir.num_entries++];
            string_copy(e->name, root_dirs[i], FM_MAX_NAME);
            e->type = FM_ENTRY_DIR;
            e->size = 4096;
            e->mode = 0755;
        }
    } else if (string_compare(path, "/home") == 0) {
        fm_entry_t* e = &fm->current_dir.entries[fm->current_dir.num_entries++];
        string_copy(e->name, "user", FM_MAX_NAME);
        e->type = FM_ENTRY_DIR;
    } else if (string_compare(path, "/etc") == 0) {
        const char* etc_files[] = { "hostname", "version", "motd", "passwd", "hosts", NULL };
        for (int i = 0; etc_files[i]; i++) {
            fm_entry_t* e = &fm->current_dir.entries[fm->current_dir.num_entries++];
            string_copy(e->name, etc_files[i], FM_MAX_NAME);
            e->type = FM_ENTRY_FILE;
            e->size = 64 + i * 16;
        }
    } else if (string_compare(path, "/bin") == 0) {
        const char* bin_files[] = {
            "sh", "ls", "cat", "cp", "mv", "rm", "vi", "asm", NULL
        };
        for (int i = 0; bin_files[i]; i++) {
            fm_entry_t* e = &fm->current_dir.entries[fm->current_dir.num_entries++];
            string_copy(e->name, bin_files[i], FM_MAX_NAME);
            e->type = FM_ENTRY_EXEC;
            e->size = 8192 + i * 4096;
            e->mode = 0755;
        }
    } else {
        /* Generic directory with some files */
        fm_entry_t* e1 = &fm->current_dir.entries[fm->current_dir.num_entries++];
        string_copy(e1->name, "file.txt", FM_MAX_NAME);
        e1->type = FM_ENTRY_FILE; e1->size = 1024;

        fm_entry_t* e2 = &fm->current_dir.entries[fm->current_dir.num_entries++];
        string_copy(e2->name, "data.bin", FM_MAX_NAME);
        e2->type = FM_ENTRY_FILE; e2->size = 4096;

        fm_entry_t* e3 = &fm->current_dir.entries[fm->current_dir.num_entries++];
        string_copy(e3->name, "subdir", FM_MAX_NAME);
        e3->type = FM_ENTRY_DIR;
    }

    /* Update path label */
    gui_set_text(fm->gui, fm->path_label_id, path);

    /* Update file list */
    gui_list_add(fm->gui, fm->file_list_id, "..");
    for (uint32_t i = 0; i < fm->current_dir.num_entries; i++) {
        char entry_buf[80];
        fm_entry_t* e = &fm->current_dir.entries[i];
        char icon = fm_get_icon(e->type, e->mode);
        string_format(entry_buf, "%c %s", icon, e->name);
        gui_list_add(fm->gui, fm->file_list_id, entry_buf);
    }

    return 0;
}

int fm_go_up(file_manager_t* fm) {
    if (!fm) return -1;
    if (string_compare(fm->cwd, "/") == 0) return 0;

    /* Find parent */
    char parent[FM_MAX_PATH];
    string_copy(parent, fm->cwd, FM_MAX_PATH);
    uint32_t len = string_length(parent);
    if (len > 1 && parent[len - 1] == '/') parent[--len] = '\0';
    while (len > 0 && parent[len - 1] != '/') len--;
    if (len > 0) parent[len] = '\0';
    else parent[0] = '/', parent[1] = '\0';

    return fm_open_dir(fm, parent);
}

int fm_go_home(file_manager_t* fm) {
    return fm ? fm_open_dir(fm, "/home/user") : -1;
}

int fm_go_to(file_manager_t* fm, const char* path) {
    return fm ? fm_open_dir(fm, path) : -1;
}

int fm_create_dir(file_manager_t* fm, const char* name) {
    if (!fm || !name) return -1;
    fm_entry_t* e = &fm->current_dir.entries[fm->current_dir.num_entries++];
    string_copy(e->name, name, FM_MAX_NAME);
    e->type = FM_ENTRY_DIR;
    e->size = 4096;
    e->mode = 0755;
    string_format(fm->status_msg, "Created directory: %s", name);
    return 0;
}

int fm_delete(file_manager_t* fm, const char* name) {
    if (!fm || !name) return -1;
    for (uint32_t i = 0; i < fm->current_dir.num_entries; i++) {
        if (string_compare(fm->current_dir.entries[i].name, name) == 0) {
            for (uint32_t j = i; j < fm->current_dir.num_entries - 1; j++)
                fm->current_dir.entries[j] = fm->current_dir.entries[j + 1];
            fm->current_dir.num_entries--;
            string_format(fm->status_msg, "Deleted: %s", name);
            return 0;
        }
    }
    return -1;
}

int fm_rename(file_manager_t* fm, const char* old_name, const char* new_name) {
    if (!fm || !old_name || !new_name) return -1;
    for (uint32_t i = 0; i < fm->current_dir.num_entries; i++) {
        if (string_compare(fm->current_dir.entries[i].name, old_name) == 0) {
            string_copy(fm->current_dir.entries[i].name, new_name, FM_MAX_NAME);
            string_format(fm->status_msg, "Renamed: %s -> %s", old_name, new_name);
            return 0;
        }
    }
    return -1;
}

int fm_copy(file_manager_t* fm, const char* name, const char* dest) {
    if (!fm) return -1;
    string_copy(fm->clipboard_path, name, FM_MAX_PATH);
    fm->clipboard_active = 1;
    fm->clipboard_is_cut = 0;
    string_format(fm->status_msg, "Copied: %s", name);
    return 0;
}

int fm_move(file_manager_t* fm, const char* name, const char* dest) {
    if (!fm) return -1;
    string_copy(fm->clipboard_path, name, FM_MAX_PATH);
    fm->clipboard_active = 1;
    fm->clipboard_is_cut = 1;
    string_format(fm->status_msg, "Cut: %s", name);
    return 0;
}

void fm_select(file_manager_t* fm, uint32_t index) {
    if (!fm || index >= fm->current_dir.num_entries) return;
    fm->current_dir.selected_idx = index;
}

void fm_select_all(file_manager_t* fm) {
    if (!fm) return;
    for (uint32_t i = 0; i < fm->current_dir.num_entries; i++)
        fm->current_dir.entries[i].selected = 1;
}

void fm_deselect_all(file_manager_t* fm) {
    if (!fm) return;
    for (uint32_t i = 0; i < fm->current_dir.num_entries; i++)
        fm->current_dir.entries[i].selected = 0;
}

void fm_set_view_mode(file_manager_t* fm, int mode) {
    if (fm) fm->current_dir.view_mode = mode;
}

void fm_toggle_hidden(file_manager_t* fm) {
    if (fm) fm->current_dir.show_hidden = !fm->current_dir.show_hidden;
}

void fm_scroll_up(file_manager_t* fm) {
    if (fm && fm->current_dir.scroll_offset > 0)
        fm->current_dir.scroll_offset--;
}

void fm_scroll_down(file_manager_t* fm) {
    if (fm) fm->current_dir.scroll_offset++;
}

char fm_get_icon(fm_entry_type_t type, uint32_t mode) {
    switch (type) {
        case FM_ENTRY_DIR:   return '/';
        case FM_ENTRY_EXEC: return '*';
        case FM_ENTRY_LINK: return '@';
        default:
            if (mode & 0x100) return '*'; /* executable bit */
            return ' ';
    }
}

void fm_render_toolbar(file_manager_t* fm) {
    /* Toolbar renders via GUI widgets */
}

void fm_render_file_list(file_manager_t* fm) {
    /* File list renders via GUI list widget */
}

void fm_render_status_bar(file_manager_t* fm) {
    gui_set_text(fm->gui, fm->status_label_id, fm->status_msg);
}

void fm_render(file_manager_t* fm) {
    if (!fm) return;
    fm_render_toolbar(fm);
    fm_render_file_list(fm);
    fm_render_status_bar(fm);
}
