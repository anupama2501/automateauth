//go:build (validation || infra.any || cluster.any || sanity) && !stress && !extended

package rbac

import (
	"fmt"
	"testing"
)

func sequentialtestRBAC() {
	fmt.Println("This function is to test the function names.")
}

func testFunctionReturnCalls() (string, string) {
	string1 := "testing1"
	string2 := "testing2"

	return string1, string2
}

func TestRBAC() {
	string1, err := testFunctionReturnCalls()

	fmt.Println(string1)

}

func VerifyPublicFunctionCalls() {
	fmt.Println("this is missing a comment")

}

