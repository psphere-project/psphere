First steps with psphere
========================

Connecting and retrieving the current server time::

    from psphere.vim25 import Vim

    vim = Vim(url)
    vim.login(username, password)
    current_time = vim.vim_service.CurrentTime(vim.si_mo_ref)
    print(current_time)
