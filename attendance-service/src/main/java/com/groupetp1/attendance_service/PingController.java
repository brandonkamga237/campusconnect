package com.groupetp1.attendance_service;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/attendance")
public class PingController {

	@GetMapping("/ping")
	public Map<String, String> ping() {
		return Map.of("service", "attendance-service", "status", "UP");
	}
}
