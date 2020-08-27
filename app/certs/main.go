/* Helper to generate self-signed certificate
 */
package main

import (
	"bytes"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io/ioutil"
	"log"
	"math/big"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"time"
)

type Input struct {
	Organization  []string
	Country       []string
	Province      []string
	Locality      []string
	StreetAddress []string
	PostalCode    []string
}

func (in *Input) UnmarshalJSON(b []byte) error {
	raw := struct {
		Organization  string
		Country       string
		Province      string
		Locality      string
		StreetAddress string
		PostalCode    string
	}{}

	if err := json.Unmarshal(b, &raw); err != nil {
		return err
	}

	convertToArray := func(word string) []string {
		wordArray := make([]string, 0, len(word))
		for _, char := range word {
			wordArray = append(wordArray, string(char))
		}
		return wordArray
	}

	in.Organization = convertToArray(raw.Organization)
	in.Country = convertToArray(raw.Country)
	in.Province = convertToArray(raw.Province)
	in.Locality = convertToArray(raw.Locality)
	in.StreetAddress = convertToArray(raw.StreetAddress)
	in.PostalCode = convertToArray(raw.PostalCode)
	return nil
}

const defaultInput = `{
	"Organization": "DigitalOnUS",
	"Country" : "US",
	"Province" : "California",
	"Locality" : "San Jose", 
	"StreetAddress" : "84 W Santa Clara Street",
	"PostalCode" : "95113"
}`

func main() {
	input := []byte(defaultInput)

	if len(os.Args) >= 2 {
		bytes, err := ioutil.ReadFile(os.Args[1])
		if err != nil {
			log.Println(err)
			os.Exit(1)
		}
		input = bytes
	}

	inputStruct := &Input{}

	if err := json.Unmarshal(input, inputStruct); err != nil {
		log.Println(err)
		os.Exit(1)
	}

	pkixName := pkix.Name{
		Organization:  inputStruct.Organization,
		Country:       inputStruct.Country,
		Province:      inputStruct.Province,
		Locality:      inputStruct.Locality,
		StreetAddress: inputStruct.StreetAddress,
		PostalCode:    inputStruct.PostalCode,
	}

	// CA certificate
	log.Println("Creating CA")
	ca := &x509.Certificate{
		SerialNumber: big.NewInt(2020),
		Subject:      pkixName,
		NotBefore:    time.Now(),
		// 2 years valid
		NotAfter:              time.Now().AddDate(2, 0, 0),
		IsCA:                  true,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth},
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
	}

	log.Println("Creating CA Private key")
	caPrivateKey, err := rsa.GenerateKey(rand.Reader, 4096)
	if err != nil {
		log.Println(err)
		os.Exit(1)
	}

	// creating the ca
	log.Println("Creating CA certificate")
	caBytes, err := x509.CreateCertificate(rand.Reader, ca, ca, &caPrivateKey.PublicKey, caPrivateKey)
	if err != nil {
		log.Println(err)
		os.Exit(1)
	}

	// pem format
	log.Println("Encoding as PEM the CA certificate")
	caPEM := new(bytes.Buffer)
	pem.Encode(caPEM, &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: caBytes,
	})

	log.Println("Encoding as PEM the CA private key")

	caPrivateKeyPEM := new(bytes.Buffer)
	pem.Encode(caPrivateKeyPEM, &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(caPrivateKey),
	})

	log.Println("Creating the server template")

	// server certificate
	serverCert := &x509.Certificate{
		SerialNumber: big.NewInt(2020),
		Subject:      pkixName,
		NotBefore:    time.Now(),
		NotAfter:     time.Now().AddDate(2, 0, 0),
		IPAddresses:  []net.IP{net.IPv4(127, 0, 0, 1), net.IPv6loopback, net.IPv4(0, 0, 0, 0)},
		SubjectKeyId: []byte{9, 8, 7, 6, 5},
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth},
		KeyUsage:     x509.KeyUsageDigitalSignature,
	}

	log.Println("Creating server private key")

	serverCertPrivateKey, err := rsa.GenerateKey(rand.Reader, 4096)
	if err != nil {
		log.Println(err)
		os.Exit(1)
	}

	log.Println("Creating server certificate")
	serverCertBytes, err := x509.CreateCertificate(rand.Reader, serverCert, ca, &serverCertPrivateKey.PublicKey, caPrivateKey)
	if err != nil {
		log.Println(err)
		os.Exit(1)
	}

	log.Println("Encoding server certificate")
	// encoding
	serverCertPEM := new(bytes.Buffer)
	pem.Encode(serverCertPEM, &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: serverCertBytes,
	})

	log.Println("Encoding server private key")
	serverCertPrivateKeyPEM := new(bytes.Buffer)
	pem.Encode(serverCertPrivateKeyPEM, &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(serverCertPrivateKey),
	})

	log.Println("Creating server x509KeyPair")
	serverCertEncoded, err := tls.X509KeyPair(serverCertPEM.Bytes(), serverCertPrivateKeyPEM.Bytes())
	if err != nil {
		log.Println(err)
		os.Exit(1)
	}

	// just for testing and check the certificates are working okay
	log.Println("-> Go setup for testing the new certs")
	serverTLSConf := &tls.Config{
		Certificates: []tls.Certificate{serverCertEncoded},
	}

	certPool := x509.NewCertPool()
	certPool.AppendCertsFromPEM(caPEM.Bytes())
	clientTLSConf := &tls.Config{
		RootCAs: certPool,
	}
	// launching and testing

	server := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "set correctly, success")
	}))

	server.TLS = serverTLSConf

	server.StartTLS()
	defer server.Close()

	// client test
	transport := &http.Transport{
		TLSClientConfig: clientTLSConf,
	}

	client := http.Client{
		Transport: transport,
	}

	fmt.Printf("****%+v\n", server.URL)

	resp, err := client.Get(server.URL)
	if err != nil {
		log.Println(err)
		return
	}

	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Println(err)
		return
	}

	body := strings.TrimSpace(string(bodyBytes))
	log.Println("response from server is ", body)
	if body != "set correctly, success" {
		log.Println("invalid response not writing the certs")
		os.Exit(1)
	}

	log.Println("Saving certificates in output directory")

	certFiles := map[string][]byte{
		"ca.cert.pem":     caPEM.Bytes(),
		"server.cert.pem": serverCertPEM.Bytes(),
		"server.key.pem":  serverCertPrivateKeyPEM.Bytes(),
	}

	for file := range certFiles {
		if err = ioutil.WriteFile(file, certFiles[file], os.ModePerm); err != nil {
			log.Println(err)
			os.Exit(1)
		}
	}

}
