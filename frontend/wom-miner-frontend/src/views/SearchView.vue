<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">

                <div class="page-header">
                    <div class="row">
                        <div class="col">
                            <h3 class="page-title">Search Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Search Page</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div id="DataTables_Table_0_filter" class="dataTables_filter">
                                <i class="fas fa-search" style="position: absolute;top: 13px;left: 10px;font-size: 14px;"></i>
                                <input v-model="searchField" class="form-control form-control-sm searchInput"
                                       placeholder="Search" type="search" @keyup.enter="search()">
                                <a class="btn btn-primary ml-1 me-1" @click="search()">
                                    <i v-if="!elastic.isSpinning" class="fas fa-search"></i>
                                    <span v-if="elastic.isSpinning" class="spinner-border spinner-border-sm me-2"></span>
                                </a>
                                <a v-if="elastic.getResult.length > 0" class="btn btn-primary filter-btn" href="javascript:void(0);" id="filter_search">
                                    <i class="fas fa-filter"></i>
                                </a>
                        </div>
                    </div>
                </div>
                <br>

                <div class="row" id="filter_inputs"  v-if="elastic.getResult.length > 0">
                    <div class="col-sm-12">
                        <div class="card">
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-sm">
                                        <div class="form-row row">
                                            <div class="col-md-3 mb-3">
                                                <label>Title & Name</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">T</span>
                                                    <input v-model="titleSearchField" class="form-control" placeholder="search" type="text">
                                                </div>
                                            </div>

                                            <div class="col-md-3 mb-3">
                                                <label>Select Type </label>
                                                <div class="input-group">
                                                    <span class="input-group-text">T</span>
                                                    <select v-model="typeFilterField" class="form-select">
                                                        <option value="-">-</option>
                                                        <option value="research project">Reseach Project</option>
                                                        <option value="faculty">Faculty</option>
                                                        <option value="chair">Chair</option>
                                                        <option value="institute">Institute</option>
                                                        <option value="people">People</option>
                                                    </select>
                                                </div>
                                            </div>

                                            <div class="col-md-3 mb-3">
                                                <label>Select University</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">{{uniFilterField.toUpperCase()}}</span>
                                                    <select  v-model="uniFilterField" class="form-select">
                                                        <option value="-">-</option>
                                                        <option value="ude">UDE</option>
                                                        <option value="rub">RUB</option>
                                                    </select>
                                                </div>
                                            </div>

                                            <div class="col-md-3 mb-3">
                                                <label>Select Language</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">{{langFilterField.toUpperCase()}}</span>
                                                    <select v-model="langFilterField" class="form-select">
                                                        <option value="-">-</option>
                                                        <option value="en">EN󠁿</option>
                                                        <option value="de">DE</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row" >
                    <div class="col-12 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Search items</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Type</th>
                                                <th>Title / Name</th>
                                                <th>Uni</th>
                                                <th>Last Update</th>
                                                <th>Language</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                        <p v-if="noEntries" class="no-entries">Sorry ... No documents found with your search Query. Try another one</p>
                                            <template v-if="elastic.getResult.length > 0">
                                                <template v-for="item in filter(resultToShow())">
                                                    <tr style="cursor: pointer" @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'research project'">
                                                            <td>{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                            <td>{{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                            <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                            <td>{{globalUtils.formatDateTime(item._source.last_update)}}</td>
                                                            <td>{{item._source.lang}}</td>
                                                        </template>
                                                        <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'people'">
                                                            <td>{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                            <td>{{item._source.name}}</td>
                                                            <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                            <td>-</td>
                                                            <td>-</td>
                                                        </template>
                                                        <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'organization'">
                                                            <td>{{globalUtils.capitalize(item._source.type)}}</td>
                                                            <td>{{item._source.name}}</td>
                                                            <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                            <td>-</td>
                                                            <td>-</td>
                                                        </template>
                                                    </tr>
                                                </template>
                                            </template>
                                        </tbody>
                                    </table>
                                </div>
                                <div class="pagination-content" v-if="!isFilterActive() && elastic.getResult.length > 0">
                                    <div>
                                        {{paginationText()}}
                                    </div>
                                    <ul class="pagination mb-4">
                                        <li class="page-item" :class="currentPagination === 1 ? 'disabled' : ''">
                                            <a class="page-link" tabindex="-1" @click="setPagination(0)" href="#">Previous</a>
                                        </li>
                                        <li class="page-item" :class="currentPagination === 1 ? 'active' : ''">
                                            <a class="page-link" @click="setPagination(1)" href="#">1</a>
                                        </li>
                                        <li class="page-item" :class="currentPagination === 2 ? 'active' : ''"
                                            v-if="elastic.getResult.length > 20">
                                            <a class="page-link" @click="setPagination(2)" href="#">2 <span class="sr-only">(current)</span></a>
                                        </li>
                                        <li class="page-item" :class="currentPagination === 3 ? 'active' : ''"
                                            v-if="elastic.getResult.length > 40">
                                            <a class="page-link" @click="setPagination(3)" href="#">3</a>
                                        </li>
                                        <li class="page-item" :class="disableNextPagination() ? 'disabled' : ''">
                                            <a class="page-link" @click="setPagination(4)" href="#">Next</a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


</template>

<script setup>
import Header from "@/components/Header.vue";
import useElasticStore from "@/stores/elastic";
import {onMounted, ref} from "vue";
import globalUtils from "@/helpers/globalUtils";
import router from "@/router";

const elastic = useElasticStore()
const searchField = ref("")
const titleSearchField = ref("")
const typeFilterField = ref("-")
const uniFilterField = ref("-")
const langFilterField = ref("-")

const currentPagination = ref(1)
const currentResult = ref([])
const noEntries = ref(false)

onMounted( () => {
    setPagination(currentPagination.value)
});

function resultToShow(){
    if(isFilterActive())
        return elastic.getResult
    return currentResult.value
}

function paginationText(){
    let from = 0
    let to = 0
    if(currentPagination.value === 1){
        from = 1
        to = elastic.getResult.length <= 20 ? elastic.getResult.length : 20
    }
    else if (currentPagination.value === 2){
        from = 21
        to = elastic.getResult.length <= 40 ? elastic.getResult.length : 40
    }
    else if (currentPagination.value === 3){
        from = 41
        to = elastic.getResult.length <= 60 ? elastic.getResult.length : 60
    }

    const entries = elastic.getResult.length <= 60 ? elastic.getResult.length : 60

    return `Showing ${from} to ${to} of ${entries} entries`
}
function isFilterActive(){
    return titleSearchField.value !== "" || typeFilterField.value !== "-" || uniFilterField.value !== "-" || langFilterField.value !== "-"
}
function disableNextPagination(){
    if(elastic.getResult.length <= 20)
        return true
    if(elastic.getResult.length > 20 && elastic.getResult.length <= 40 && currentPagination.value === 2)
        return true
    return (elastic.getResult.length >= 40 && currentPagination.value === 3);
}

function setPagination(pagination){
    if(pagination === 0 && currentPagination.value !== 1)
        currentPagination.value --
    else if(pagination === 4 && currentPagination.value !== 3)
        currentPagination.value ++
    else
        currentPagination.value = pagination

    if(currentPagination.value === 1)
        currentResult.value = elastic.getResult.slice(0, 20)
    else if(currentPagination.value === 2)
        currentResult.value = elastic.getResult.slice(20, 40)
    else
        currentResult.value = elastic.getResult.slice(40, 60)
}
function titleFilter(itemList) {
    return itemList.filter(item => {
        let toCompare = ""
        if(globalUtils.extractTypeFromIndex(item._index) === "people")
            toCompare = item._source.name
        else if(globalUtils.extractTypeFromIndex(item._index) === "research project")
            toCompare = item._source.title
        else
            toCompare = item._source.name

        return toCompare.toLowerCase().includes(titleSearchField.value.toLowerCase())
    })
}

function typeFilter(itemList) {
    if (typeFilterField.value === "-")
        return itemList

    return itemList.filter(item => {
        if(!item._source.type)
            return true
        return item._source.type.toLowerCase().includes(typeFilterField.value.toLowerCase())
    })
}

function uniFilter(itemList) {
    if (uniFilterField.value === "-")
        return itemList

    return itemList.filter(item => {
        return globalUtils.extractUniFromIndex(item._index).toLowerCase().includes(uniFilterField.value.toLowerCase())
    })
}

function langFilter(itemList) {
    if (langFilterField.value === "-")
        return itemList

    return itemList.filter(item => {
        if(!item._source.lang)
            return true
        return item._source.lang.toLowerCase().includes(langFilterField.value.toLowerCase())
    })
}

function filter(expenseList) {
    if(isFilterActive())
        return titleFilter(typeFilter(langFilter(uniFilter(expenseList))))
    return expenseList
}


async function search() {
    currentPagination.value = 1
    elastic.resetResult()
    let params = {
        endpoint: "/research_project-ude/_search",
        searchField: searchField.value
    }
    await elastic.fetchResearchMinerDocuments(params)

    params.endpoint = "/research_project-rub/_search"
    await elastic.fetchResearchMinerDocuments(params)

    params.endpoint = "/people-ude/_search"
    await elastic.fetchPeopleMinerDocuments(params)

    params.endpoint = "/people-rub/_search"
    await elastic.fetchPeopleMinerDocuments(params)

    params.endpoint = "/org-ude/_search"
    await elastic.fetchOrgMinerDocuments(params)

    params.endpoint = "/org-rub/_search"
    await elastic.fetchOrgMinerDocuments(params)

    currentResult.value = elastic.getResult.slice(0,20)

    noEntries.value = elastic.getResult.length === 0;
}


</script>

<style scoped>
th {
    cursor: pointer;
}

.ml-1 {
    margin-left: 10px;
}

.searchInput {
    margin-left: 0;
    display: inline-block;
    width: 50%;
    padding-left: 30px;
    border: 1px solid #e5e5e5;
    color: #1b2559;
    height: 40px;
    border-radius: 8px;
}

.pagination-content {
    display: flex;
    margin: 25px 30px 0 30px;
    justify-content: space-between;
}

.no-entries {
    margin: 20px;
    color: #f60808;
}

</style>