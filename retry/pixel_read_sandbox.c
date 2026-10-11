/* Linux x86_64 pixel actor supervisor: immutable read roots, no network or children.
 * This same-host sandbox is for a frozen, single-thread actor, not hostile code.
 * The parent resolves paths and ptrace denies opens outside the supplied roots.
 * seccomp traces only open/exec, so observation IPC does not incur ptrace stops.
 */
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>
#include <stddef.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static pid_t child;
static char **roots; static int nroots;
static void stop(int sig) { (void)sig; if(child>0){kill(child,SIGKILL); waitpid(child,0,0);} _exit(125); }
static int strread(unsigned long addr,char *out) {
  for(size_t i=0;i<PATH_MAX;i+=sizeof(long)) {
    errno=0; long v=ptrace(PTRACE_PEEKDATA,child,(void*)(addr+i),0);
    if(errno)return -1;
    size_t n=sizeof(long); if(i+n>PATH_MAX)n=PATH_MAX-i;
    memcpy(out+i,&v,n); if(memchr(&v,0,n))return 0;
  } return -1;
}
static int allowed(unsigned long ptr,int dirfd) {
  char path[PATH_MAX],full[PATH_MAX],canon[PATH_MAX],base[PATH_MAX],link[80];
  if(strread(ptr,path))return 0;
  if(path[0]=='/') { if(strlen(path)>=sizeof full)return 0; strcpy(full,path); }
  else {
    if(dirfd==AT_FDCWD)snprintf(link,sizeof link,"/proc/%d/cwd",child);
    else snprintf(link,sizeof link,"/proc/%d/fd/%d",child,dirfd);
    ssize_t n=readlink(link,base,sizeof(base)-1); if(n<0)return 0; base[n]=0;
    if(snprintf(full,sizeof full,"%s/%s",base,path)>=(int)sizeof full)return 0;
  }
  if((strstr(full,"/proc/") && strcmp(full,"/proc/cpuinfo") && strcmp(full,"/proc/meminfo")) || strstr(full,"/dev/fd/"))return 0;
  if(!realpath(full,canon))return 0;
  for(int i=0;i<nroots;i++) {
    size_t n=strlen(roots[i]);
    if(!strncmp(canon,roots[i],n) && (!canon[n]||canon[n]=='/'))return 1;
  }
  const char *exact[]={"/etc/ld.so.cache","/etc/localtime","/dev/null","/dev/urandom","/dev/random","/proc/cpuinfo","/proc/meminfo",NULL};
  for(int i=0;exact[i];i++)if(!strcmp(canon,exact[i]))return 1;
  return 0;
}
#define STMT(c,k) ((struct sock_filter)BPF_STMT(c,k))
#define JUMP(c,k,t,f) ((struct sock_filter)BPF_JUMP(c,k,t,f))
static int filter(void) {
  struct sock_filter f[256]; unsigned n=0;
  f[n++]=STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch));
  f[n++]=JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_X86_64,1,0);
  f[n++]=STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS);
  f[n++]=STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr));
  f[n++]=JUMP(BPF_JMP|BPF_JGE|BPF_K,0x40000000,0,1);
  f[n++]=STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS);
  int trace[]={SYS_open,SYS_openat,SYS_execve};
  for(unsigned i=0;i<sizeof(trace)/sizeof(*trace);i++){
    f[n++]=JUMP(BPF_JMP|BPF_JEQ|BPF_K,trace[i],0,1);
    f[n++]=STMT(BPF_RET|BPF_K,SECCOMP_RET_TRACE);
  }
  int deny[]={SYS_openat2,SYS_creat,SYS_execveat,SYS_socket,SYS_socketpair,SYS_connect,SYS_bind,SYS_listen,SYS_accept,SYS_accept4,SYS_sendto,SYS_sendmsg,SYS_recvmsg,SYS_recvmmsg,SYS_sendmmsg,
  SYS_clone,SYS_clone3,SYS_fork,SYS_vfork,SYS_ptrace,SYS_process_vm_readv,SYS_process_vm_writev,SYS_pidfd_getfd,SYS_open_by_handle_at,SYS_name_to_handle_at,SYS_io_uring_setup,SYS_io_uring_enter,SYS_io_uring_register,
  SYS_unlink,SYS_unlinkat,SYS_rename,SYS_renameat,SYS_renameat2,SYS_link,SYS_linkat,SYS_symlink,SYS_symlinkat,SYS_mkdir,SYS_mkdirat,SYS_rmdir,SYS_truncate,SYS_ftruncate,SYS_chmod,SYS_fchmod,SYS_fchmodat,SYS_chown,SYS_fchown,SYS_lchown,SYS_fchownat,SYS_mknod,SYS_mknodat,SYS_mount,SYS_umount2,SYS_pivot_root,SYS_chroot,SYS_setns,SYS_unshare,SYS_kill,SYS_tkill,SYS_tgkill,SYS_bpf,SYS_perf_event_open,SYS_userfaultfd};
  for(unsigned i=0;i<sizeof(deny)/sizeof(*deny);i++){
    f[n++]=JUMP(BPF_JMP|BPF_JEQ|BPF_K,deny[i],0,1);
    f[n++]=STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EACCES);
  }
  f[n++]=STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW);
  struct sock_fprog p={.len=n,.filter=f};
  return prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)||prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&p);
}
int main(int argc,char **argv) {
  int sep=1; while(sep<argc&&strcmp(argv[sep],"--"))sep++;
  if(sep==1||sep+1>=argc)return 2;
  roots=argv+1;nroots=sep-1;
  char exe[PATH_MAX]; if(!realpath(argv[sep+1],exe))return 2;
  for(int i=0;i<nroots;i++){char p[PATH_MAX];if(!realpath(roots[i],p))return 2;roots[i]=strdup(p);}
  child=fork(); if(child<0)return 2;
  if(!child){
    for(int fd=3;fd<1024;fd++)close(fd);
    if(ptrace(PTRACE_TRACEME,0,0,0))_exit(120);
    raise(SIGSTOP); if(filter())_exit(121);
    execv(argv[sep+1],argv+sep+1);_exit(122);
  }
  signal(SIGTERM,stop);signal(SIGINT,stop);
  fprintf(stderr,"PIXEL_SANDBOX_ACTOR_PID=%d\n",child); fflush(stderr);
  int status; if(waitpid(child,&status,0)<0)return 3;
  if(ptrace(PTRACE_SETOPTIONS,child,0,PTRACE_O_EXITKILL|PTRACE_O_TRACESECCOMP|PTRACE_O_TRACESYSGOOD))stop(0);
  int firstexec=1,denying=0; if(ptrace(PTRACE_CONT,child,0,0))stop(0);
  while(waitpid(child,&status,0)>0){
    if(WIFEXITED(status))return WEXITSTATUS(status);
    if(WIFSIGNALED(status))return 128+WTERMSIG(status);
    if(!WIFSTOPPED(status))continue;
    int sig=WSTOPSIG(status),deliver=0;struct user_regs_struct r;
    if((status>>16)==PTRACE_EVENT_SECCOMP){
      if(ptrace(PTRACE_GETREGS,child,0,&r))stop(0);
      int ok=0;
      if(r.orig_rax==SYS_execve){char p[PATH_MAX],c[PATH_MAX];ok=firstexec&&!strread(r.rdi,p)&&realpath(p,c)&&!strcmp(c,exe);firstexec=0;}
      else {unsigned long flags=r.orig_rax==SYS_open?r.rsi:r.rdx;unsigned long p=r.orig_rax==SYS_open?r.rdi:r.rsi;int d=r.orig_rax==SYS_open?AT_FDCWD:(int)r.rdi;
        ok=!(flags&(O_WRONLY|O_RDWR|O_CREAT|O_TRUNC|O_APPEND))&&allowed(p,d);}
      if(!ok){r.orig_rax=-1;if(ptrace(PTRACE_SETREGS,child,0,&r))stop(0);denying=1;if(ptrace(PTRACE_SYSCALL,child,0,0))stop(0);continue;}
    } else if(sig==(SIGTRAP|0x80)&&denying){
      if(ptrace(PTRACE_GETREGS,child,0,&r))stop(0);
      r.rax=-EACCES;if(ptrace(PTRACE_SETREGS,child,0,&r))stop(0);denying=0;
    } else if(sig!=SIGTRAP)deliver=sig;
    if(ptrace(PTRACE_CONT,child,0,deliver))stop(0);
  } return 4;
}
