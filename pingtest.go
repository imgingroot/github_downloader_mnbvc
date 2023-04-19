package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"sort"
	"sync"
	"time"
)

type ipSpeed struct {
	ip          string
	speed       int
	isConnected bool
}

type ipSpeeds []ipSpeed

func (ips ipSpeeds) Len() int           { return len(ips) }
func (ips ipSpeeds) Swap(i, j int)      { ips[i], ips[j] = ips[j], ips[i] }
func (ips ipSpeeds) Less(i, j int) bool { return ips[i].speed < ips[j].speed }
func testIPSpeed(hostname string, ip string) ipSpeed {
	start := time.Now()
	// 确保使用指定的IP来访问指定的域名
	transport := &http.Transport{
		DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			dialer := &net.Dialer{
				Timeout:   5 * time.Second,
				KeepAlive: 5 * time.Second,
				DualStack: true,
			}
			conn, err := dialer.DialContext(ctx, network, fmt.Sprintf("%s:%s", ip, "443"))
			if err != nil {
				return nil, err
			}
			return conn, nil
		},
	}
	client := &http.Client{Transport: transport, Timeout: 5 * time.Second}
	_, err := client.Get("https://" + hostname)
	elapsed := int(time.Since(start).Milliseconds())
	if err == nil {
		return ipSpeed{
			ip:          ip,
			speed:       elapsed,
			isConnected: true,
		}
	}

	return ipSpeed{
		ip:          ip,
		speed:       elapsed,
		isConnected: false,
	}
}

func testDomainIPs(hostname string, ips []string) (string, ipSpeeds, error) {
	var wg sync.WaitGroup
	var speeds ipSpeeds
	for _, ip := range ips {
		wg.Add(1)
		go func(ip string) {
			defer wg.Done()
			speed := testIPSpeed(hostname, ip)
			if speed.isConnected {
				speeds = append(speeds, speed)
			}
		}(ip)
	}

	wg.Wait()
	if len(speeds) > 0 {
		sort.Sort(speeds)
		return speeds[0].ip, speeds, nil
	} else {
		return "", nil, fmt.Errorf("all IPs are not reachable")
	}
}
