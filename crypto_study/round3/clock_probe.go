package main
import("encoding/json";"os";"syscall";"time";"unsafe")
func main(){
 dll:=syscall.NewLazyDLL("kernel32.dll");counter:=dll.NewProc("QueryPerformanceCounter");frequency:=dll.NewProc("QueryPerformanceFrequency")
 var f int64;ok,_,_:=frequency.Call(uintptr(unsafe.Pointer(&f)));if ok==0||f<=0{panic("frequency")}
 now:=func()int64{var n int64;ok,_,_:=counter.Call(uintptr(unsafe.Pointer(&n)));if ok==0{panic("counter")};return n}
 const n=20000
 wallZero:=0;qpcZero:=0;wallMin:=int64(1<<62);qpcMin:=int64(1<<62);qpcSum:=int64(0)
 for i:=0;i<n;i++{a:=time.Now();b:=time.Now();d:=b.Sub(a).Nanoseconds();if d==0{wallZero++}else if d<wallMin{wallMin=d}}
 for i:=0;i<n;i++{a:=now();b:=now();d:=b-a;qpcSum+=d;if d==0{qpcZero++}else if d<qpcMin{qpcMin=d}}
 json.NewEncoder(os.Stdout).Encode(map[string]interface{}{"pairs":n,"time_now_zero_pairs":wallZero,"time_now_min_positive_ns":wallMin,"qpc_zero_pairs":qpcZero,"qpc_frequency":f,"qpc_min_positive_ticks":qpcMin,"qpc_mean_pair_ns":float64(qpcSum)*1e9/float64(f*n)})
}
