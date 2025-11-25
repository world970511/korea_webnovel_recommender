T = int(input())
ans_list=[]
for test_case in range(1, T + 1):
    #######################################################################################################
	N = int(input())
	l = list(input().split())
	ans_list=[]
	for i in range(0,len(I)):
		for j in  range(i,len(I)):
            if l[i]!=l[j]:
                if l[i]>l[j]:
                    ans_list.append(l[i])
                ans_list.append(l[j])
	ans=sum(ans_list)
    #######################################################################################################
    # 표준출력(화면)으로 답안을 출력합니다.
    print("#%d" % test_case, end=' ')
    print(ans, end=' ')