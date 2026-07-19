package config

import "testing"

func TestValidate(t *testing.T) {
	tests := []struct {
		name    string
		s       Settings
		wantErr bool
	}{
		{"valid", Settings{Environment: EnvProduction, Port: 8000, LogFormat: "auto"}, false},
		{"bad environment", Settings{Environment: "bogus", Port: 8000, LogFormat: "auto"}, true},
		{"port too low", Settings{Environment: EnvDevelopment, Port: 0, LogFormat: "auto"}, true},
		{"port too high", Settings{Environment: EnvDevelopment, Port: 70000, LogFormat: "auto"}, true},
		{"bad log format", Settings{Environment: EnvDevelopment, Port: 8000, LogFormat: "xml"}, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.s.Validate()
			if (err != nil) != tt.wantErr {
				t.Fatalf("Validate() error = %v, wantErr = %v", err, tt.wantErr)
			}
		})
	}
}

func TestUseJSONLogs(t *testing.T) {
	tests := []struct {
		name string
		s    Settings
		want bool
	}{
		{"auto in development is console", Settings{Environment: EnvDevelopment, LogFormat: "auto"}, false},
		{"auto in production is json", Settings{Environment: EnvProduction, LogFormat: "auto"}, true},
		{"explicit json overrides development", Settings{Environment: EnvDevelopment, LogFormat: "json"}, true},
		{"explicit console overrides production", Settings{Environment: EnvProduction, LogFormat: "console"}, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.s.UseJSONLogs(); got != tt.want {
				t.Errorf("UseJSONLogs() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestLoadDefaults(t *testing.T) {
	t.Setenv("ASKP_ENVIRONMENT", "staging")
	t.Setenv("ASKP_PORT", "9090")

	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if s.Environment != EnvStaging {
		t.Errorf("Environment = %q, want staging", s.Environment)
	}
	if s.Port != 9090 {
		t.Errorf("Port = %d, want 9090", s.Port)
	}
	if s.AppName != "askp" {
		t.Errorf("AppName = %q, want default askp", s.AppName)
	}
	if s.Addr() != "127.0.0.1:9090" {
		t.Errorf("Addr() = %q, want 127.0.0.1:9090", s.Addr())
	}
}
