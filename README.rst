=================
 RollbackContext 
=================
------------------------------------------------
 A Context Manager to Do Rollback Automatically
------------------------------------------------

Purpose
=======
Sometimes we need to perform a series of operations::

 op[0], op[1], ... op[N]

These operations may allocate files, locks, connections, and ``op[K]`` may depend on result of ``op[K-1]``. Each operation creates a context. When the operations are done, we want to destroy those contexts. Sometimes it's not feasible to use standard Python Context Manager Protocol, because the number of the resource involved in a transaction can be a variable. There is no way to use a variable number of the ``with`` statement, and ``contextlib.nested`` is being deprecated. Sometimes it's just too verbose to create standard Python Context Manager for each context.

This library implements a concise Context Manager and proposes an idiom for rollback.

How It Works
============
It allows the programme register an undo function after each successful operation. It manages the undo functions as a stack. Each new undo function is push to the top of the stack. When the the operations are successful and execution flow leaves the context manager, it tries to pop the undo functions and run them. In all, it runs the following operation series::

 op[0], op[1], ... op[N], DONE, -op[N], ... , -op[1], -op[0]

If there is an exception from ``op[X]``, it aborts the execution of the op series and starts to run undos. If there is an exception from the undos, it ignores the exception temporary and continues to run the rest of the undos. At last, it re-raises the earliest exception it sees. This is because latter exceptions may be caused by an earlier exception, so the most helpful exception for diagnosing the problem is the earliest one. Meanwhile, it should execute all the undos to destroy all the contexts as much as possible.

How to Use
==========
0. Run as superuser, ``easy_install rollbackcontext`` or ``pip install rollbackcontext``.
1. In Python, ``from rollbackcontext import RollbackContext``.
2. Use it in a ``with`` statement as following:

::

 with RollbackContext() as rollback:

3. Write code for the operations, after each operation success, register a reverse operation by calling the ``push`` method.

::

 with RollbackContext() as rollback:
     op0
     rollbcak.push(op0Reverse)
     op1
     rollbcak.push(op1Reverse)

The ``push`` method accepts callable and the arguments that would be passed to the callable.

Examples
========
A most simple example may be the following::

 from sys import stdout
 
 from rollbackcontext import RollbackContext
 
 with RollbackContext() as rollback:
     print "Op 0"
     rollback.push(lambda: stdout.write("Undo 0\n"))
     print "Op 1"
     rollback.push(lambda: stdout.write("Undo 1\n"))
     print "Op 2"
     rollback.push(lambda: stdout.write("Undo 2\n"))
 # Prints the following
 # Op 0
 # Op 1
 # Op 2
 # Undo 2
 # Undo 1
 # Undo 0

You can refer to unit test code to find many more examples.

Here are some examples from simplified production code::

 def vm_lifecycle(...):
     ''' The task is to create the VM, perform some tests and
     destroy the VM and related resources. '''
     with RollbackContext() as rollback:
         templates_create('testTemplate', ...)
         rollback.push(template_delete, 'testTemplate')
 
         vms_create('testVM', ...)
         rollback.push(vm_delete, 'testVM')
 
         vm_start('testVM', ...)
         rollback.push(vm_stop, 'testVM')
 
         # Do whatever with the VM

Another one::

 def prepare(...):
     ''' The task is to detect if a NFS export could be mounted or not. '''
     with RollbackContext() as rollback:
         mnt_point = tempfile.mkdtemp(dir='/tmp')
         rollback.push(os.rmdir, mnt_point)
 
         mount_cmd = ["mount", ..., mnt_point]
         run_command(mount_cmd, 30)
         umount_cmd = ["umount", "-f", mnt_point]
         rollback.push(run_command, umount_cmd)
 
         # Do whatever with the mounted filesystem

Yet another one::

 def probe_user(self):
     ''' The task is to start a libvirt domain and detect the user id of the
     VM process. '''
     user = None
     with RollbackContext() as rollback:
         conn = libvirt.open('qemu:///system')
         rollback.push(conn.close)
         dom = conn.defineXML('...')
         rollback.push(dom.undefine)
         dom.create()
         rollback.push(dom.destroy)
         with open('/var/run/libvirt/qemu/%s.pid' % self.vm_name) as f:
             pidStr = f.read()
         p = psutil.Process(int(pidStr))
         user = p.username
     return user

The above code comes from `project kimchi <https://github.com/kimchi-project/kimchi>`_, a HTML5 based management tool for KVM.

More Helpful Features
=====================

Cancel All Rollbacks
--------------------
Most of the time we need to run all the undos, but sometimes we want to cancel the undos if all operations are successful. In this case, call the ``commitAll`` method to cancel all the undos as following::

 with RollbackContext() as rollback:
     print 'Op 0'
     rollback.push(op0Reverse)
     print 'Op 1'
     rollback.push(op1Reverse)
     rollback.commitAll()

Cancel a Particular Rollback
----------------------------
Sometimes we want to cancel a particular undo if all operations are successful. In this case, call the ``setAutoCommit`` method of the object returned from the ``push`` method.

::

 with RollbackContext() as rollback:
    print 'Op 0'
    rollback.push(op0Reverse).setAutoCommit()
    print 'Op 1'
    rollback.push(op1Reverse)

If any exception would be raised within the ``with`` statement, ``op1Reverse`` and ``op2Reverse`` would be run. If the ``with`` statement was successful, only ``op1Reverse`` would be run.

Register Undo Function to the Bottom of the Stack
-------------------------------------------------
Normally the ``push`` method adds the undo function to the top of the undo stack. In case you want to insert undo function to the bottom of the undo stack, use the ``pushBottom`` method.

::

 from sys import stdout
 
 
 with RollbackContext() as rollback:
     rollback.pushBottom(lambda: stdout.write("0\n"))
     rollback.pushBottom(lambda: stdout.write("1\n"))
     rollback.pushBottom(lambda: stdout.write("2\n"))
 # Should print
 # 0
 # 1
 # 2

Anti-pattern Examples
=====================
Unfortunately, C programmers can not enjoy the delight from our RollbackContext, they have to detect error code of each operation and use ``goto out0``, ``goto out1``, and so on, to simulate our RollbackContext manually. The following function comes from Linux kernel source code::

 static int __init init_nfs_fs(void)
 {
 	int err;
 
 	err = register_pernet_subsys(&nfs_net_ops);
 	if (err < 0)
 		goto out9;
 
 	err = nfs_fscache_register();
 	if (err < 0)
 		goto out8;
 
 	err = nfsiod_start();
 	if (err)
 		goto out7;
 
 	err = nfs_fs_proc_init();
 	if (err)
 		goto out6;
 
 	err = nfs_init_nfspagecache();
 	if (err)
 		goto out5;
 
 	err = nfs_init_inodecache();
 	if (err)
 		goto out4;
 
 	err = nfs_init_readpagecache();
 	if (err)
 		goto out3;
 
 	err = nfs_init_writepagecache();
 	if (err)
 		goto out2;
 
 	err = nfs_init_directcache();
 	if (err)
 		goto out1;
 
 #ifdef CONFIG_PROC_FS
 	rpc_proc_register(&init_net, &nfs_rpcstat);
 #endif
 	if ((err = register_nfs_fs()) != 0)
 		goto out0;
 
 	return 0;
 out0:
 #ifdef CONFIG_PROC_FS
 	rpc_proc_unregister(&init_net, "nfs");
 #endif
 	nfs_destroy_directcache();
 out1:
 	nfs_destroy_writepagecache();
 out2:
 	nfs_destroy_readpagecache();
 out3:
 	nfs_destroy_inodecache();
 out4:
 	nfs_destroy_nfspagecache();
 out5:
 	nfs_fs_proc_exit();
 out6:
 	nfsiod_stop();
 out7:
 	nfs_fscache_unregister();
 out8:
 	unregister_pernet_subsys(&nfs_net_ops);
 out9:
 	return err;
 }

If this function was to be written in Python (of course it never would), we could re-structure it as the following::

 def init_nfs_fs():
     with RollbackContext() as rollback:
         op0
         rollback.push(op0Reverse)
         op1
         rollback.push(op1Reverse)
         # ...
         rollback.commitAll()

It would be more cleaner. Whenever you find yourself dealing with similar case in Python, nesting ``try...finally`` blocks, you might want to have a go on RollbackContext.

For more anti-pattern examples, you can just ``git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git``, and ``git grep 'goto out5'``, ``git grep 'goto out6'`` and more. Currently the worst case is ``bfin_lq035q1_probe`` function in ``drivers/video/bfin-lq035q1-fb.c``, it ``goto out10``.
